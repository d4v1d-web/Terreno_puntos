"""
topo_utils.py - Módulo de Cálculo Numérico y Geométrico Vial
"""
import numpy as np
import scipy.spatial as spatial
import scipy.interpolate as interpolate
import scipy.ndimage as ndimage

def generar_datos_ejemplo(n_puntos=800):
    np.random.seed(42)
    X = np.random.uniform(100, 600, n_puntos)
    Y = np.random.uniform(100, 600, n_puntos)
    Z = 2500 + 0.05 * X + 0.03 * Y + 15 * np.sin(X/80) * np.cos(Y/80)
    Z += np.random.normal(0, 1.5, n_puntos)
    codigos = np.random.choice(["TN", "TERRENO", "BORDE"], n_puntos)
    indices = np.arange(1, n_puntos + 1)
    return indices, X, Y, Z, codigos

def filtrar_triangulos_delaunay(X, Y, max_longitud):
    pts = np.vstack((X, Y)).T
    tri = spatial.Delaunay(pts)
    simplices = tri.simplices
    triangulos_validos = []
    aristas_unicas = set()
    for sim in simplices:
        p1, p2, p3 = pts[sim[0]], pts[sim[1]], pts[sim[2]]
        if np.linalg.norm(p1 - p2) <= max_longitud and np.linalg.norm(p2 - p3) <= max_longitud and np.linalg.norm(p3 - p1) <= max_longitud:
            triangulos_validos.append(sim)
            for ar in [tuple(sorted((sim[0], sim[1]))), tuple(sorted((sim[1], sim[2]))), tuple(sorted((sim[2], sim[0])))]:
                aristas_unicas.add(ar)
    return np.array(triangulos_validos), list(aristas_unicas)

def generar_mde(X, Y, Z, triangulos_validos, resolucion=50):
    x_min, x_max = X.min(), X.max()
    y_min, y_max = Y.min(), Y.max()
    grid_x, grid_y = np.meshgrid(np.linspace(x_min, x_max, resolucion), np.linspace(y_min, y_max, resolucion))
    grid_z = interpolate.griddata((X, Y), Z, (grid_x, grid_y), method='linear')
    return grid_x, grid_y, grid_z

def calcular_maqueta_volumen(grid_x, grid_y, grid_z, cota_base):
    dx = grid_x[0, 1] - grid_x[0, 0]
    dy = grid_y[1, 0] - grid_y[0, 0]
    return np.sum(grid_z[~np.isnan(grid_z)] - cota_base) * (dx * dy)

def disenar_eje_vial(puntos_control, sigma=2.0, num_estaciones=200):
    pts = np.array(puntos_control)
    t = np.linspace(0, 1, len(pts))
    t_fino = np.linspace(0, 1, num_estaciones)
    x_smooth = ndimage.gaussian_filter1d(np.interp(t_fino, t, pts[:, 0]), sigma) if sigma > 0 else np.interp(t_fino, t, pts[:, 0])
    y_smooth = ndimage.gaussian_filter1d(np.interp(t_fino, t, pts[:, 1]), sigma) if sigma > 0 else np.interp(t_fino, t, pts[:, 1])
    x_smooth[0], y_smooth[0] = pts[0, 0], pts[0, 1]
    x_smooth[-1], y_smooth[-1] = pts[-1, 0], pts[-1, 1]
    pks = np.concatenate(([0], np.cumsum(np.sqrt(np.diff(x_smooth)**2 + np.diff(y_smooth)**2))))
    return np.vstack((x_smooth, y_smooth)).T, pks

def calcular_perfil_y_rasante(eje_xy, pks, X, Y, Z, pendientes_tramos):
    tree = spatial.cKDTree(np.vstack((X, Y)).T)
    _, idx = tree.query(eje_xy)
    z_terreno = Z[idx]
    z_rasante = np.zeros_like(pks)
    z_rasante[0] = z_terreno[0]
    for i in range(1, len(pks)):
        tr = min(int(pks[i] // 100), len(pendientes_tramos) - 1)
        z_rasante[i] = z_rasante[i-1] + (pks[i] - pks[i-1]) * (pendientes_tramos[tr] / 100.0)
    return z_terreno, z_rasante

def cubicacion_obra_tierra(pks, z_terreno, z_rasante, ancho_via, talud_corte, talud_relleno):
    h = z_terreno - z_rasante
    a_c = np.array([(ancho_via + talud_corte * abs(hi)) * abs(hi) if hi >= 0 else 0.0 for hi in h])
    a_r = np.array([(ancho_via + talud_relleno * abs(hi)) * abs(hi) if hi < 0 else 0.0 for hi in h])
    v_c, v_r = np.zeros_like(pks), np.zeros_like(pks)
    for i in range(1, len(pks)):
        ds = pks[i] - pks[i-1]
        v_c[i] = v_c[i-1] + ((a_c[i-1] + a_c[i]) / 2.0) * ds
        v_r[i] = v_r[i-1] + ((a_r[i-1] + a_r[i]) / 2.0) * ds
    return a_c, a_r, v_c, v_r
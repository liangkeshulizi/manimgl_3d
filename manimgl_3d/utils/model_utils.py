import numpy as np

def compute_tangents(vertices: np.ndarray, tex_coords: np.ndarray, normals: np.ndarray, face_indices: np.ndarray) -> np.ndarray:
    '''Compute the tangent vectors (per vertex) of a 3D model based on its texture coordinates.
    Calculating the tangent vectors is not as straightforward as the normal vector.
    See: https://learnopengl.com/Advanced-Lighting/Normal-Mapping'''

    assert vertices.shape[1] == 3 and tex_coords.shape[1] == 2 and face_indices.shape[1] == 3

    # let n = number of faces, v = number of vertices
    
    index1, index2, index3 = face_indices.transpose()
    vertex1, vertex2, vertex3 = vertices[index1], vertices[index2], vertices[index3]
    tex1, tex2, tex3 = tex_coords[index1], tex_coords[index2], tex_coords[index3]
    
    vector1_xyz = vertex2 - vertex1     # shape = (n, 3)
    vector2_xyz = vertex3 - vertex1     # shape = (n, 3)

    vector1_uv = tex2 - tex1    # shape = (n, 2)
    vector2_uv = tex3 - tex1    # shape = (n, 2)

    mat_xyz = np.stack((vector1_xyz, vector2_xyz), axis=-1)   # shape = (n, 3, 2)
    mat_uv = np.stack((vector1_uv, vector2_uv), axis=-1)      # shape = (n, 2, 2)

    mat_uv_inv = np.linalg.inv(mat_uv)
    uv = mat_xyz @ mat_uv_inv

    tangent_per_face = uv[:, :, 0]   # the matrix consists of [tangent_xyz, bitangent_xyz]  (as column vectors)
    
    # Accumulate tangent (per face) to the face vertices
    tangent_per_vertex = np.zeros_like(vertices)            # shape = (v, 3)
    for index in (index1, index2, index3):
        np.add.at(tangent_per_vertex, index, tangent_per_face)

    # Ensure the tangent vectors is perpendicular to the normal vectors
    tangent_per_vertex -= np.sum(tangent_per_vertex * normals, axis=1, keepdims=True) * normals

    return tangent_per_vertex

def np_normalize(vectors: np.ndarray):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


# Test Script
if __name__ == "__main__":
    import trimesh

    # FILEPATH = "./assets/coffee-cup/obj/coffee_cup_obj.obj"
    FILEPATH = "./assets/cone/Cone.obj"

    # Load the mesh
    mesh: trimesh.Trimesh = trimesh.load(file_obj=FILEPATH)

    # Prepare data and normalize
    normals = mesh.vertex_normals
    vertices = mesh.vertices
    tex_coords = mesh.visual.uv
    faces = mesh.faces
    tangent = compute_tangents(vertices, tex_coords, normals, faces)
    
    normals = np_normalize(normals)
    tangent = np_normalize(tangent)

    # ---------- Draw Normals ----------

    length = 0.05
    lines_n = np.hstack([
        vertices,
        vertices + normals * length
    ]).reshape(-1, 2, 3)

    normal_arrows = trimesh.load_path(lines_n)

    # ---------- Draw Tangents ----------

    lines_t = np.hstack([
        vertices,
        vertices + tangent * length
    ]).reshape(-1, 2, 3)
    tangent_arrows = trimesh.load_path(lines_t)

    # ---------- Draw Triangles ----------

    triangles = mesh.triangles  # shape (num_faces, 3, 3)

    edges = np.concatenate([
        triangles[:, [0, 1]],
        triangles[:, [1, 2]],
        triangles[:, [2, 0]]
    ], axis=0)  # shape (3 * num_faces, 2, 3)

    triangle_edges = trimesh.load_path(edges)

    # ---------- Construct Scene ----------

    scene = trimesh.Scene()
    scene.add_geometry(mesh)
    scene.add_geometry(normal_arrows)
    # scene.add_geometry(tangent_arrows)
    scene.add_geometry(triangle_edges)

    # Show the scene
    scene.show()

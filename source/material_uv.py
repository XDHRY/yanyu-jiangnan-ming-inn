"""Grain-aligned UVs for solid timber, including batches of separate rafters."""
import numpy as np
import trimesh


def timber_uv(mesh, split_components=False):
    vertices=mesh.vertices[mesh.faces].reshape(-1,3)
    normals=np.repeat(mesh.face_normals,3,axis=0)
    out=np.zeros((len(vertices),2))
    groups=trimesh.graph.connected_components(mesh.face_adjacency,nodes=np.arange(len(mesh.faces)),min_len=1) if split_components else [np.arange(len(mesh.faces))]
    for group in groups:
        indices=(np.asarray(group)[:,None]*3+np.arange(3)).reshape(-1)
        points=vertices[indices]
        center=points.mean(axis=0)
        _,axes=np.linalg.eigh((points-center).T@(points-center))
        # Fix eigenvector sign so exports are deterministic across clean builds.
        for k in range(3):
            dominant=np.argmax(abs(axes[:,k]))
            if axes[dominant,k]<0:axes[:,k]*=-1
        if np.linalg.det(axes)<0:axes[:,0]*=-1
        local=(points-center)@axes
        local_normals=normals[indices]@axes
        normal_axis=np.argmax(abs(local_normals),axis=1)
        for k in range(3):
            selected=normal_axis==k
            plane=[a for a in range(3) if a!=k]
            # The texture grain runs vertically: its V axis follows the timber.
            if 2 in plane:plane=[a for a in plane if a!=2]+[2]
            out[indices[selected]]=local[selected][:,plane]/np.array([.45,1.4])
    return out

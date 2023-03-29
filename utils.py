import math
from math import cos, sin
import numpy as np


def get_distance(p, q, coef_tab):
    """
    Retourne la distance entre deux points p et q qui ont le meme nombre de dimension

    On assume que coeff_tab est la longeur de p et q
    si pas de pondération : coef_tab = [1 in range(0,len(q))]
    """
    sum_sq_difference = 0
    for p_i, q_i, coeff_i in zip(p, q, coef_tab):
        sum_sq_difference += coeff_i * ((p_i - q_i) ** 2)

    distance = sum_sq_difference ** 0.5
    return distance


def convert_effort(fx, fy, fz, freq_rotation, angle_radial, angle_axial, angle_attaque):
    """Fonction qui convertie les efforts à la pièce en effort à la dent de l'outil

    Parameters
    ----------
    fx : float
        effort fx à la pièce
    fy : float
        effort fy à la pièce
    fz : float
        effort fz à la pièce
    freq_rotation : float
        frequence de rotation de l'outil en tr/min
    angle_radial : float
        angle radial de l'outil en radian
    angle_axial : float
        angle axial de l'outil en radian
    angle_attaque : float
        angle d'attaque de l'outil en radian

    Returns
    ----------
    fx_outil : float
        effort fx à l'outil
    fy_outil : float
        effort fy à l'outil
    fz_outil : float
        effort fz à l'outil
    """

    angle = (freq_rotation * math.pi) / 30

    # matrice de passage 1
    passage_1 = np.array([
        [cos(angle), sin(angle), 0],
        [-sin(angle), cos(angle), 0],
        [0, 0, 1]
    ])

    # matrice de passage 2
    passage_2 = np.array([
        [cos(angle_radial), sin(angle_radial), 0],
        [-sin(angle_radial), cos(angle_radial), 0],
        [0, 0, 1]
    ])

    # matrice de passage 3
    passage_3 = np.array([
        [1, 0, 0],
        [0, cos(angle_axial), sin(angle_axial)],
        [0, -sin(angle_axial), cos(angle_axial)]
    ])

    # matrice de passage 4
    passage_4 = np.array([
        [cos(angle_attaque), 0, sin(angle_attaque)],
        [-sin(angle_attaque), 0, cos(angle_attaque)],
        [0, 1, 0]
    ])

    effort_piece = np.array([[fx], [fy], [fz]])

    coord_1 = np.dot(passage_1, effort_piece)

    coord_2 = np.dot(passage_2, coord_1)

    coord_3 = np.dot(passage_3, coord_2)

    coord_4 = np.dot(passage_4, coord_3)

    fx_outil = coord_4[0, 0]
    fy_outil = coord_4[1, 0]
    fz_outil = coord_4[2, 0]

    return fx_outil, fy_outil, fz_outil


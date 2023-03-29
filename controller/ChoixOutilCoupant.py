import numpy as np
import pandas as pd
from tkinter.messagebox import showerror, showinfo
import plotly.express as px
from sklearn.decomposition import PCA
from sqlalchemy import and_
import model
from model.Experience import Experience
from model.Entree_piece import Entree_piece
from model.Sortie_piece import Sortie_piece
from model.Vibration import Vibration
from model.Entree_outil import Entree_outil
from model.Effort_outil import Effort_outil
from model.Usure_outil import Usure_outil
from model.Procede import Procede
from model.Temperature_outil import Temperature_outil
from model import session
from utils import get_distance
import plotly.graph_objs as go


class ChoixOutilCoupant:
    """Classe qui contient les méthodes nécéssaire au choix de l'outil coupant"""

    def __init__(self):
        self.values_container = None
        self.ids_exp = None
        self.exp_nouns = None
        self.pca = None
        self.components = None
        self.classes_df = None
        self.fig_2d = None
        self.fig_3d = None
        self.features = None
        self.loadings = None
        self.total_var = None
        self.form_datas = None
        self.var_explained = []

    def create_pca_dataframes(self, form_datas):
        """Méthode créant et retournant le tableau utile afin de réaliser l'ACP

        Parameters:
            -form_datas: dictionnaire contentant les informations remplises par l'utilsateur lors de la page
                            choix outil coupant

        Returns:
            -dataframe: contient le tableau pour faire l'acp
        """

        # Récuperer le formulaire rempli par l'utilisateur
        self.form_datas = form_datas

        ids_by_procede = [x[0] for x in session.query(Procede.id_experience).filter(
            Procede.type_procede == self.form_datas['procede'])
            .distinct(Procede.id_experience)]

        ids_by_materiau = [x[0] for x in session.query(Entree_piece.id_experience).filter(
            Entree_piece.materiaux == self.form_datas['materiau'])
            .distinct(Entree_piece.id_experience)]

        # Récuperer les id d'expériences correspondant au champs requis pour l'ACP
        self.ids_exp = list(set(ids_by_procede) & set(ids_by_materiau))

        # Affichage d'un message d'erreur si aucune experience ne correspond
        if not self.ids_exp:
            showerror(title="Erreur", message="Aucune expérience correspondant au couple "
                                              + "(" + self.form_datas['procede'] + "/"
                                              + self.form_datas['materiau'] + ")"
                                              + " est recensée dans la base de données")

        # Récuperer des noms des expériences en vu d'un éventuel affichage
        self.exp_nouns = [x for x in session.query(Experience.id_experience, Experience.nom
                                                   ).filter(Experience.id_experience.in_(self.ids_exp))]

        # Récuperer les informations des tables entree_piece
        info_ep_df = self.get_info_ep()

        # Récuperer les efforts max à l'outil
        info_effort_outil_max_df = self.get_info_effort_coupe_max_df()

        # Récuperer les températures max à l'outil
        info_temp_outil_max_df = self.get_info_temp_max_df()

        # Récuperer les sorties max à la pièce
        info_sortie_piece_max_df = self.get_info_sortie_piece_max_df()

        # Récuperer le temps d'usinage max
        info_temps_usinage_max_df = self.get_info_temps_usinage_max_df()

        # Récuperer les amplitudes max
        info_amplitude_max_df = self.get_info_amplitude_max_df()

        session.close()

        # Récuperer les infos du formulaire rempli par l'utilisateur dans un dataframe
        choix_user = self.get_user_df()

        # print(choix_user)

        # Concaténation des infos des différentes expériences récuperer
        data_db_df = pd.concat([info_ep_df, info_effort_outil_max_df, info_temp_outil_max_df, info_sortie_piece_max_df,
                                info_temps_usinage_max_df, info_amplitude_max_df], axis=1, sort=False)

        # Ajout du point de réference utilisateur
        pca_df = pd.concat([data_db_df.drop(columns=["ID"]), choix_user], ignore_index=True,
                           sort=False)


        self.values_container = pca_df

        pca_df = pca_df.dropna(axis=1, how='all').replace(to_replace=np.nan, value=0)

        return pca_df

    def compute_pca(self, form_datas):
        """ Fonction calculant l'ACP

        tab: list contenant les informations principales des éxpériences les plus proches
        """
        pca_df = self.create_pca_dataframes(form_datas)

        # 2D si deux variables/individus ou moins, 3D sinon
        self.n_components = min(len(pca_df.columns), len(pca_df))
        self.pca = PCA(n_components=self.n_components)
        self.components = self.pca.fit_transform(pca_df)
        self.loadings = self.pca.components_.T * np.sqrt(self.pca.explained_variance_)

        self.features = [col_name for col_name in pca_df.columns]  # nom des variables prises en comptes pour l'acp

        explained_variances = self.pca.explained_variance_ratio_
        for i, ev in enumerate(explained_variances):
            print(f"\nAxis {i + 1}: Explained variance = {ev:.2%}")
            # Récupération des charges factorielles pour chaque axe
            loadings = self.loadings[:, i]
            # Triage des variables par contribution décroissante à l'axe
            sorted_loadings_idx = np.argsort(np.abs(loadings))[::-1]
            sorted_loadings = loadings[sorted_loadings_idx]
            sorted_features = np.array(self.features)[sorted_loadings_idx]

            var = []
            # Affichage des 5 variables les plus contributives à l'axe
            for j in range(0, self.n_components):
                var.append(sorted_features[j] + " : " + str(
                    round(abs((sorted_loadings[j] * 100)) / np.sum(abs(sorted_loadings)), 2)) + "%")
            self.var_explained.append(var)

        return self.compute_closest_experiences()

    def create_and_display_fig_3d(self):
        """ Créé la modèlisation de l'ACP en 3d"""
        # print(self.pca.components_)
        if self.pca.n_components < 3:
            showinfo(title="Info", message="L'ACP ne contient pas assez de composantes pour être affichée en 3D")
        else:
            if not self.fig_2d:
                # On calcule le taux d'information contenu dans le graphique 3
                self.total_var = self.pca.explained_variance_ratio_[:3].sum() * 100
                col = [i for i in range(self.n_components)]
                if len(self.components) == 2:
                    labels = ['x', 'y']
                elif len(self.components) == 3:
                    labels = ['x', 'y', 'z']
                elif len(self.components) > 3:
                    labels = ['x', 'y', 'z', 't']

                final_data = pd.DataFrame(self.components, columns=col, index=labels)

                for column in self.values_container.columns:
                    final_data.loc[column] = self.values_container[column].values

                final_data = final_data.round(4)
                final_data = final_data.T

                self.fig_3d = px.scatter_3d(
                    final_data, x='x', y='y', z='z',
                    title=f'Total Explained Variance: {self.total_var:.2f}%',
                    hover_data=self.features
                )

                self.fig_3d.update_layout(scene=dict(
                    xaxis_title="Factorial axe n°1: {}% ".format(round(self.pca.explained_variance_ratio_[0] * 100, 2)),
                    yaxis_title="Factorial axe n°2: {}% ".format(round(self.pca.explained_variance_ratio_[1] * 100, 2)),
                    zaxis_title="Factorial axe n°3: {}% ".format(round(self.pca.explained_variance_ratio_[2] * 100, 2)))
                )
                self.fig_3d.add_trace(
                    go.Scatter3d(
                        x=[final_data.iloc[len(final_data) - 1, 0]],
                        y=[final_data.iloc[len(final_data) - 1, 1]],
                        z=[final_data.iloc[len(final_data) - 1, 2]],
                        mode="text",
                        text=["Point Utilisateur"],
                        textposition="bottom right"
                    )
                )
            display_fig(self.fig_3d)

    def create_and_display_fig_2d(self, with_variable=False):
        """ Créé la modèlisation de l'ACP en 2d avec ou sans les variables

        Parameters:
            with_variable: Boolean pour savoir si on doit ajouter les variables au graph"""

        # if TYPE_LUBRIFIANT in self.classes_df:
        #     # On calcule le taux d'information contenu dans le graphique 2
        self.total_var = self.pca.explained_variance_ratio_[:2].sum() * 100

        col = [i for i in range(self.n_components)]
        if len(self.components) == 2:
            labels = ['x', 'y']
        elif len(self.components) == 3:
            labels = ['x', 'y', 'z']
        elif len(self.components) > 3:
            labels = ['x', 'y', 'z', 't']

        final_data = pd.DataFrame(self.components, columns=col, index=labels)

        for column in self.values_container.columns:
            final_data.loc[column] = self.values_container[column].values

        final_data = final_data.round(4)
        final_data = final_data.T

        self.fig_2d = px.scatter(
            final_data, x='x', y='y',
            title=f'Total Explained Variance: {self.total_var:.2f}%',
            hover_data=self.features
        )

        self.fig_2d.update_layout(
            xaxis_title="Factorial axe n°1: {}% ".format(round(self.pca.explained_variance_ratio_[0] * 100, 2)),
            yaxis_title="Factorial axe n°2: {}% ".format(round(self.pca.explained_variance_ratio_[1] * 100, 2)),
        )

        self.fig_2d.add_trace(
            go.Scatter(
                x=[final_data.iloc[len(final_data) - 1, 0]],
                y=[final_data.iloc[len(final_data) - 1, 1]],
                mode="text",
                text=["Point Utilisateur"],
                textposition="bottom right"
            )
        )

        self.fig_2d.add_annotation(
            x=0.5,
            y=-0.13,
            showarrow=False,
            text=f"{[str(i).replace('nan', '0') for i in self.var_explained[0]]}",
            xref="paper",
            yref="paper",
            font=dict(
                size=14,
                color="black"
            )
        )

        # Add y-axis label annotation
        self.fig_2d.add_annotation(
            x=-0.08,
            y=0.5,
            showarrow=False,
            text=f"{[str(i).replace('nan', '0') for i in self.var_explained[1]]}",
            textangle=-90,
            xref="paper",
            yref="paper",
            font=dict(
                size=14,
                color="black"
            )
        )

        self.fig_2d.update_layout(margin=dict(l=100, r=100))

        if with_variable:
            for i, feature in enumerate(self.features):
                self.fig_2d.add_shape(
                    type='line',
                    x0=0, y0=0,
                    x1=self.loadings[i, 0],
                    y1=self.loadings[i, 1]
                )
                self.fig_2d.add_annotation(
                    x=self.loadings[i, 0],
                    y=self.loadings[i, 1],
                    ax=0, ay=0,
                    xanchor="center",
                    yanchor="bottom",
                    text=feature,
                )
        display_fig(self.fig_2d)

    def compute_closest_experiences(self):
        """Fonction qui calcule le tableau récapitulant les expériences les plus proches

        Returns:
            tab: list contenant les informations principales des éxpériences les plus proches"""

        tab = []
        exp_user = self.components[-1]  # Les coordonées du point de l'utilisateur sont toujours en dernier
        # print('exp_user :\t', exp_user, '\n')

        dist = []
        for exp_coord in self.components[:-1]:
            dist.append(get_distance(exp_user, exp_coord, self.pca.explained_variance_ratio_))

        dist = np.array(dist)
        # print('dist :\t', dist, '\n')

        sorted_dist = dist.argsort()

        nb_rows = len(sorted_dist) if len(sorted_dist) < 10 else 10
        # print('sorted_dist :\t', sorted_dist, '\n')
        for index in sorted_dist[:nb_rows]:

            mycursor = model.mydb.cursor()

            max_fx_piece = 0
            max_fy_piece = 0
            max_fz_piece = 0
            tmp_max_piece = 0

            max_fx_outil = 0
            max_fy_outil = 0
            max_fz_outil = 0
            tmp_max_outil = 0

            max_amplitude = 0
            max_freq = 0

            sql1 = """select nom from experience where id_experience = %s"""
            mycursor.execute(sql1, (self.ids_exp[index],))
            experience = mycursor.fetchall()

            sql2 = """select * from procede where id_experience = %s"""
            mycursor.execute(sql2, (self.ids_exp[index],))
            procede = mycursor.fetchall()

            sql3 = """select * from entree_piece where id_experience = %s"""
            mycursor.execute(sql3, (self.ids_exp[index],))
            entree_piece = mycursor.fetchall()

            sql4 = """select * from entree_outil where id_experience = %s"""
            mycursor.execute(sql4, (self.ids_exp[index],))
            entree_outil = mycursor.fetchall()

            sql5 = """select * from effort_piece where id_entree_piece = %s"""
            mycursor.execute(sql5, (entree_piece[0][0],))
            effort_piece = mycursor.fetchall()

            if len(effort_piece) == 0:
                max_fx_piece = None
                max_fy_piece = None
                max_fz_piece = None
            else:
                for x in effort_piece:
                    if abs(x[2]) > abs(max_fx_piece):
                        max_fx_piece = x[2]
                    if abs(x[3]) > abs(max_fy_piece):
                        max_fy_piece = x[3]
                    if abs(x[4]) > abs(max_fz_piece):
                        max_fz_piece = x[4]

            sql6 = """select * from temperature_piece where id_entree_piece = %s"""
            mycursor.execute(sql6, (entree_piece[0][0],))
            tmp_piece = mycursor.fetchall()
            if len(tmp_piece) == 0:
                tmp_max_piece = None
            else:
                for x in tmp_piece:
                    if abs(x[2]) > abs(tmp_max_piece):
                        tmp_max_piece = x[2]

            sql7 = """select * from sortie_piece where id_entree_piece = %s"""
            mycursor.execute(sql7, (entree_piece[0][0],))
            sortie_piece = mycursor.fetchall()
            if len(sortie_piece) == 0:
                sortie_piece_1 = None
                sortie_piece_2 = None
                sortie_piece_3 = None
                sortie_piece_4 = None
            else:
                sortie_piece_1 = sortie_piece[0][1]
                sortie_piece_2 = sortie_piece[0][2]
                sortie_piece_3 = sortie_piece[0][3]
                sortie_piece_4 = sortie_piece[0][4]

            sql8 = """select * from effort_outil where id_entree_outil = %s"""
            mycursor.execute(sql8, (entree_outil[0][0],))
            effort_outil = mycursor.fetchall()

            if len(effort_outil) == 0:
                max_fx_outil = None
                max_fy_outil = None
                max_fz_outil = None
            else:
                for x in effort_outil:
                    if abs(x[2]) > abs(max_fx_outil):
                        max_fx_outil = x[2]
                    if abs(x[3]) > abs(max_fy_outil):
                        max_fy_outil = x[3]
                    if abs(x[4]) > abs(max_fz_outil):
                        max_fz_outil = x[4]

            sql9 = """select * from temperature_outil where id_entree_outil = %s"""
            mycursor.execute(sql9, (entree_outil[0][0],))
            tmp_outil = mycursor.fetchall()
            if len(tmp_outil) == 0:
                tmp_max_outil = None
            else:
                for x in tmp_outil:
                    if x[2] > tmp_max_outil:
                        tmp_max_outil = x[2]

            sql10 = """select * from usure_outil where id_entree_outil = %s"""
            mycursor.execute(sql10, (entree_outil[0][0],))
            usure_outil = mycursor.fetchall()
            if len(usure_outil) == 0:
                usure_outil_1 = None
                usure_outil_2 = None
                usure_outil_3 = None
            else:
                usure_outil_1 = usure_outil[0][2]
                usure_outil_2 = usure_outil[0][3]
                usure_outil_3 = usure_outil[0][4]

            sql11 = """select * from copeaux where id_experience = %s"""
            mycursor.execute(sql11, (self.ids_exp[index],))
            copeaux = mycursor.fetchall()

            if len(copeaux) == 0:
                copeaux_1 = None
            else:
                copeaux_1 = copeaux[0][1]

            sql12 = """select * from vibration where (id_entree_outil = %s AND id_entree_piece = %s)"""
            mycursor.execute(sql12, (entree_outil[0][0], entree_piece[0][0]))
            vibration = mycursor.fetchall()

            if len(vibration) == 0:
                max_amplitude = None
                max_freq = None
            else:
                for x in vibration:
                    if abs(x[3]) > abs(max_amplitude):
                        max_amplitude = x[3]
                    if abs(x[2]) > abs(max_freq):
                        max_freq = x[2]

            tab.append((self.ids_exp[index], experience[0][0], procede[0][1],
                        procede[0][2], procede[0][3], procede[0][4], procede[0][5],
                        procede[0][6], procede[0][7], procede[0][8], procede[0][10],
                        procede[0][11], entree_piece[0][1], entree_piece[0][2],
                        entree_piece[0][3], entree_piece[0][4], entree_piece[0][5],
                        entree_piece[0][6], max_fx_piece, max_fy_piece, max_fz_piece,
                        tmp_max_piece, sortie_piece_1, sortie_piece_2,sortie_piece_3,
                        sortie_piece_4, entree_outil[0][1],
                        entree_outil[0][2], entree_outil[0][3], entree_outil[0][4],
                        entree_outil[0][5], max_fx_outil, max_fy_outil,
                        max_fz_outil, tmp_max_outil, usure_outil_1, usure_outil_2,
                        usure_outil_3, copeaux_1, max_freq, max_amplitude,
                        round(dist[index], 3)))
        # print('tab :\t', tab, '\n')
        return tab

    def get_max_per_exp(self, info_multi_row_per_exp_df):
        """Fonction qui renvoie le maximum en valeur absolue sur chaque colonne du dataframe par id d'expérience

        Params: info_multi_row_per_exp_df: dataframe

        Returns: dataframe"""
        if info_multi_row_per_exp_df.empty:
            return None
        else:
            dataframes = []
            for id in self.ids_exp:
                sub_df = info_multi_row_per_exp_df.query('ID == {}'.format(id))
                dataframes.append(sub_df.abs().max().to_frame().T)

            return pd.concat(dataframes, ignore_index=True, sort=False)

    def get_info_effort_coupe_max_df(self):
        """Renvoie le dataframe associé aux efforts maximals de chaque compsosantes de chaque expérience

        Returns: dataframe or None"""

        if any(key in self.form_datas for key in ['fx', 'fy', 'fz']):
            info_effort_coupe = [x for x in session.query(Entree_outil.id_experience,
                                                          Effort_outil.fx if 'fx' in self.form_datas else None,
                                                          Effort_outil.fy if 'fy' in self.form_datas else None,
                                                          Effort_outil.fz if 'fz' in self.form_datas else None
                                                          ).join(Entree_outil).filter(
                Entree_outil.id_experience.in_(self.ids_exp))]
            # Déduire les variables supplémentaire de l'ACP (Max/min/mean)
            info_effort_coupe_df = pd.DataFrame(info_effort_coupe, columns=["ID",
                                                                            'fx' if 'fx' in self.form_datas else None,
                                                                            'fy' if 'fy' in self.form_datas else None,
                                                                            'fz' if 'fz' in self.form_datas else None])
            # print('efforts :\n', info_effort_coupe_df)
            info_effort_coupe_max_df = self.get_max_per_exp(
                info_effort_coupe_df.dropna(axis=1, how='all').replace(to_replace=np.nan, value=0))

            return info_effort_coupe_max_df
        return None

    def get_info_temp_max_df(self):
        """Renvoie le dataframe associé aux efforts maximals de chaque compsosantes de chaque expérience

        Returns: dataframe or None"""

        if any(key in self.form_datas for key in ['temperature']):
            info_temperature = [x for x in session.query(Entree_outil.id_experience,
                                                         Temperature_outil.temperature_outil if 'temperature' in self.form_datas else None
                                                         ).join(Entree_outil).filter(
                Entree_outil.id_experience.in_(self.ids_exp))]
            # Déduire les variables supplémentaire de l'ACP (Max/min/mean)
            info_temperature_df = pd.DataFrame(info_temperature, columns=["ID",
                                                                          'temperature' if 'temperature' in self.form_datas else None])
            info_effort_coupe_max_df = self.get_max_per_exp(
                info_temperature_df.dropna(axis=1, how='all').replace(to_replace=np.nan, value=0))

            return info_effort_coupe_max_df
        return None

    def get_info_sortie_piece_max_df(self):
        """Renvoie le dataframe associé aux efforts maximals de chaque compsosantes de chaque expérience

        Returns: dataframe or None"""

        if any(key in self.form_datas for key in ['contraintes_residuelles', 'durete', 'fatigue', 'rugosite']):
            info_sortie_piece = [x for x in session.query(Entree_piece.id_experience,
                                                          Sortie_piece.contrainte_residuelle if 'contraintes_residuelles' in self.form_datas else None,
                                                          Sortie_piece.durete if 'durete' in self.form_datas else None,
                                                          Sortie_piece.limite_endurance if 'fatigue' in self.form_datas else None,
                                                          Sortie_piece.rugosite if 'rugosite' in self.form_datas else None
                                                          ).join(Entree_piece).filter(
                Entree_piece.id_experience.in_(self.ids_exp))]
            # Déduire les variables supplémentaire de l'ACP (Max/min/mean)
            info_sortie_piece_df = pd.DataFrame(info_sortie_piece, columns=["ID",
                                                                            'contraintes_residuelles' if 'contraintes_residuelles' in self.form_datas else None,
                                                                            'durete' if 'durete' in self.form_datas else None,
                                                                            'fatigue' if 'fatigue' in self.form_datas else None,
                                                                            'rugosite' if 'rugosite' in self.form_datas else None])
            info_sortie_piece_max_df = self.get_max_per_exp(
                info_sortie_piece_df.dropna(axis=1, how='all').replace(to_replace=np.nan, value=0))

            return info_sortie_piece_max_df
        return None

    def get_info_temps_usinage_max_df(self):
        """Calcul les informations de la table Rugoisté en faisant une moyenne par expérience

        Returns:
            dataframe or None"""

        if 'temps_usinage' in self.form_datas:
            info_temp = [x for x in session.query(Entree_outil.id_experience,
                                                  Usure_outil.temps_usinage).join(Entree_outil)
                .filter(Entree_outil.id_experience.in_(self.ids_exp))]
            # Déduire les variables supplémentaire de l'ACP (Max/min/mean)
            info_temp_df = pd.DataFrame(info_temp, columns=["ID", 'temps_usinage'])
            info_temp_max_df = self.get_max_per_exp(info_temp_df)

            return info_temp_max_df
        return None

    def get_info_amplitude_max_df(self):
        """Renvoie le dataframe associé aux efforts maximals de chaque compsosantes de chaque expérience

        Returns: dataframe or None"""

        if 'amplitude' in self.form_datas:
            info_vibration = [x for x in session.query(Entree_piece.id_experience,
                                                       Vibration.amplitude)
                .select_from(Entree_piece)
                .join(Entree_outil, and_(Entree_outil.id_experience == Entree_piece.id_experience))
                .join(Vibration, and_(Vibration.id_entree_piece == Entree_piece.id_entree_piece,
                                      Vibration.id_entree_outil == Entree_outil.id_entree_outil))
                .filter(Entree_piece.id_experience.in_(self.ids_exp))]

            # Déduire les variables supplémentaire de l'ACP (Max/min/mean)
            info_vibration_df = pd.DataFrame(info_vibration, columns=["ID",
                                                                      'amplitude' if 'amplitude' in self.form_datas else None])
            info_vibration_max_df = self.get_max_per_exp(
                info_vibration_df.dropna(axis=1, how='all').replace(to_replace=np.nan, value=0))

            return info_vibration_max_df
        return None

    def get_info_ep(self):
        """Renvoie les informations sur les conditions de coupe des expériences

        Returns:
            dataframe"""

        info_ep = [x for x in session.query(Entree_piece.id_experience,
                                            Entree_piece.longueur_usinee if 'longueur_usine' in self.form_datas else None).filter(
            Entree_piece.id_experience.in_(self.ids_exp)).
            distinct(Entree_piece.id_experience)]

        info_ep_df = pd.DataFrame(info_ep,
                                  columns=["ID",
                                           'longueur_usine' if 'longueur_usine' in self.form_datas else None])
        # print(info_ep_df)
        return info_ep_df.dropna(axis=1, how="all").replace(to_replace=np.nan, value=0)

    def get_user_df(self):
        """Renvoie le dataframe correspondant aux choix du l'utilisteur dans le formulaire

        Returns:
            dataframe"""

        user_df = pd.DataFrame(self.form_datas, index=[0])

        user_df.drop(
            columns=['procede', 'materiau'],
            inplace=True,
        )

        return user_df


def display_fig(fig):
    """Affiche la figure sur le navigateur"""

    if fig is not None:
        fig.show()
    else:
        showerror(title="Erreur", message="La figure est vide")

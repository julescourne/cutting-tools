from tkinter import Frame, Button, BOTH, YES, Canvas, Label, Menu, Toplevel, CURRENT, NORMAL, DISABLED
from PIL import ImageTk, Image



class MenuView:
    """Classe qui gère la vue de la page d'accueil"""

    def __init__(self, window, background_image):
        """Constructeur de la fenêtre Accueil

        Parameters
        ----------
        window : Tk
            La fenêtre principale de l'application
        background_image : PhotoImage
            L'objet qui prend une image en argument

        """
        # titre fenetre
        window.title("Accueil")

        # taille fenetre
        window.geometry("1080x760")
        # taille min
        window.minsize(480, 360)

        # icone fenetre
        window.iconbitmap('images/logo.ico')

        self.frame_menu = Frame(window)
        self.frame_menu.pack(fill=BOTH, expand=YES)

        # création canvas
        self.canvas_menu = Canvas(self.frame_menu, width=1080, height=720)
        self.canvas_menu.pack(fill="both", expand=True)

        self.canvas_menu.create_image(0, 0, image=background_image, anchor="nw")

        # ajout logos
        self.logo_univ = ImageTk.PhotoImage(
            Image.open("images/UnivTours-Logo horizontal.jpg").resize((138, 50), Image.ANTIALIAS))
        self.label_logo_univ = Label(self.canvas_menu, image=self.logo_univ)
        self.label_logo_univ.place(relx=1.0, rely=0.0, anchor="ne")
        self.logo_ceroc = ImageTk.PhotoImage(
            Image.open("images/Ceroc logo 2020.jpg").resize((153, 50), Image.ANTIALIAS))
        self.label_logo_ceroc = Label(self.canvas_menu, image=self.logo_ceroc)
        self.label_logo_ceroc.place(relx=1.0, rely=0.09, anchor="ne")

        # ajout boutons
        self.frame_import = Frame(self.canvas_menu)
        self.butt_import = Button(self.frame_import, text="Importer données", font=("Arial", 30), bg='white',
                                  fg='black')
        self.butt_import.pack()
        self.frame_import.pack(pady=30)

        self.frame_outil = Frame(self.canvas_menu)
        self.butt_outil = Button(self.frame_outil, text="Choisir outil coupant", font=("Arial", 30), bg='white',
                                 fg='black')
        self.butt_outil.pack()
        self.frame_outil.pack(pady=30)

        # Créer le menu principal
        menu_bar = Menu(window)
        window.config(menu=menu_bar)

        # Créer un menu Aide avec une option Aide en ligne
        self.aide_menu = Menu(menu_bar, tearoff=0)
        self.aide_menu.add_command(label="Aide Importer", command=self.ouvrir_fenetre_aide_importer)
        self.aide_menu.add_command(label="Aide Choix Outil Coupant", command=self.ouvrir_fenetre_aide_choix)
        self.aide_menu.add_command(label="Aide Résultat Choix Outil Coupant", command=self.ouvrir_fenetre_aide_resultat)
        menu_bar.add_cascade(label="Aide", menu=self.aide_menu)


    def ouvrir_fenetre_aide_importer(self):
        """Fonction pour ouvrir une fenetre d'aide"""
        fenetre_aide = Toplevel()
        fenetre_aide.title("Fenêtre d'aide importation")
        message_aide = "Le bouton importer permet d'importer un fichier Excel contenant les données d'une expérience d'usinage.\n"
        message_aide += "Le fichier Excel doit avoir un format bien précis.\n"
        message_aide += 'Les données importées sont ajoutés en base de données et deviennent accessible.'
        message_label = Label(fenetre_aide, text=message_aide, font=("Arial", 12))
        message_label.pack(padx=10, pady=10)

    def ouvrir_fenetre_aide_choix(self):
        """Fonction pour ouvrir une fenetre d'aide"""
        fenetre_aide = Toplevel()
        fenetre_aide.title("Fenêtre d'aide")
        message_aide = "Sur cette fenêtre vous pouvez choisir vos conditions de coupe dans le but d'obtenir un outils coupant adéquat.\n"
        message_aide += "Vous pouvez chosir vos conditions sur l'outil d'usinage, la pièce à usiner et sur les interactions entre l'outil et la pièce.\n"
        message_aide += 'Les champs "procédé d\'usinage" et "matériau usiné" sont à remplir obligatoirement. '
        message_aide += "Outre ces deux champs, vous devez à minima remplir trois autres champs."
        message_label = Label(fenetre_aide, text=message_aide, font=("Arial", 12))
        message_label.pack(padx=10, pady=10)

    def ouvrir_fenetre_aide_resultat(self):
        """Fonction pour ouvrir une fenetre d'aide"""
        fenetre_aide = Toplevel()
        fenetre_aide.title("Fenêtre d'aide page de résultat de choix d'un outil coupant")
        message_aide = "Sur cette fenêtre obtenez le résultat pour les conditions de coupes remplis\n\n"
        message_aide += "Vous avez un tableau récapitulatif des expériences similaires aux conditions voulus.\n"
        message_aide += "L'expérience en haut de tableau est l'expérience la plus proche des conditions voulus.\n"
        message_aide += "Vous pouvez cliquer sur une experience pour ouvrir une interface et visualiser l'expérience\n\n"
        message_aide += 'Le champs \'outils coupant conseillé\' correspond à l\'outil coupant utilisé pour l\'expérience la plus proche\n\n'
        message_aide += 'Les deux boutons ACP 2D et ACP 3D ouvrent un graphique dynamique affichant le résultat des ACP.\n'
        message_aide += 'Chaque graphique contient le point des conditions voulus, les points des expériences similaires et l\'explication des variables\n'
        message_label = Label(fenetre_aide, text=message_aide, font=("Arial", 12))
        message_label.pack(padx=10, pady=10)

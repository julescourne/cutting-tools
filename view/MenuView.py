from tkinter import Frame, Button, BOTH, YES, Canvas, Label
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
        window.geometry("1080x720")
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

        # self.frame_conditions = Frame(self.canvas_menu)
        # self.butt_conditions = Button(self.frame_conditions, text="Choisir conditions de coupe", font=("Arial", 30),
        #                               bg='white', fg='black')
        # self.butt_conditions.pack()
        # self.frame_conditions.pack(pady=30)

        self.frame_outil = Frame(self.canvas_menu)
        self.butt_outil = Button(self.frame_outil, text="Choisir outil coupant", font=("Arial", 30), bg='white',
                                 fg='black')
        self.butt_outil.pack()
        self.frame_outil.pack(pady=30)

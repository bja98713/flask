# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
#import matplotlib
#import matplotlib.pyplot as plt
#from io import BytesIO
#import base64
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
#from flask_migrate import Migrate
#from utils import format_date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activite.db'
app.config['SECRET_KEY'] = '677868767867867'  # Changez cela par une vraie clé secrète
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class Activite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    numero_semaine = db.Column(db.Integer)
    numero_facture = db.Column(db.Integer, nullable=False)
    dn = db.Column(db.Integer, nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    date_naissance = db.Column(db.Date, nullable=False)
    numero_telephone = db.Column(db.String(20), nullable=True)
    mail = db.Column(db.String(30), nullable=True)
    acte = db.Column(db.String(100), nullable=False)
    modalite_paiement = db.Column(db.String(50), nullable=False)
    paiement = db.Column(db.Integer, nullable=False)
    observation = db.Column(db.String(255))
    paiement_cps = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Activite(id={self.id}, date={self.date}, dn={self.dn}, nom={self.nom}, prenom={self.prenom}, ...)"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


@app.route('/')
@login_required
def index():
    #print('Nom de l\'utilisateur connecté:', current_user.username)
    activites = Activite.query.all()
    return render_template('index.html', activites=activites, format_date=format_date)

def format_date(date):
    return date.strftime('%d/%m/%Y')

@app.route('/ajouter', methods=['POST'])
def ajouter():
    data = request.form

    date_str = data['date'].strip()
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

    #if not date_obj or not data['numero_facture'] or not data['dn'] or not data['nom'] or not data['prenom'] or not data['date_naissance'] or not data['acte'] or not data['modalite_paiement']:
    #   return redirect(url_for('index'))

    numero_semaine = date_obj.isocalendar()[1]

    mapping_paiement_cps = {
        'CS': 0,
        'CS_LM': 4370,
        'ZCQM005': 10672,
        'ZCQM005_H': 0,
        'ZCQM005_LM': 15245
    }

    mapping_paiement = {
        'CS_H': 3910,
        'CS' : 4600,
        'CS_LM' : 4600,
        'CS_MGEN' : 4370,
        'ZCQM005' : 15245,
        'ZCQM005_LM' : 15245,
        'ZCQM005_H': 12958,
        'ZCQM005_MGEN' : 14483,
        'HEQE002/2+HHQE002': 40657,
        'HEQE002/2+HHFE006' : 50425,
        'HEQE002/2+HHFE002' : 48402,
        'HGQE003/2+HHQE002': 45910,
        'HHFE002' : 30976,
        'HEQE002' : 19361,
        'HHFE002' : 30976,
        'HESE002' : 27351,
        'HEAE003' : 24605,
        'HHQE002' : 30976,
        'HFKE001' : 21007,
        'HHGE002' : 21843
    }

    existing_activite = Activite.query.filter_by(dn=data['dn']).first()

    if existing_activite:
        #eturn render_template('index.html', activites=Activite.query.all(), format_date=format_date, dn_existe=True)
        
        
        nouvelle_activite = Activite(
            date=date_obj,
            numero_semaine=numero_semaine,
            numero_facture=data['numero_facture'],
            dn=data['dn'],
            nom=existing_activite.nom,
            prenom=existing_activite.prenom,
            date_naissance=existing_activite.date_naissance,
            numero_telephone=existing_activite.numero_telephone,
            mail=existing_activite.mail,
            acte=data['acte'],
            modalite_paiement=data['modalite_paiement'],
            paiement=mapping_paiement.get(data['acte'], 0),
            observation=data['observation'],
            paiement_cps=mapping_paiement_cps.get(data['acte'], 0)
        )
    else:
        nouvelle_activite = Activite(
            date=date_obj,
            numero_semaine=numero_semaine,
            numero_facture=data['numero_facture'],
            dn=data['dn'],
            nom=data['nom'],
            prenom=data['prenom'],
            date_naissance=datetime.strptime(data['date_naissance'], '%Y-%m-%d').date(),
            numero_telephone=data['numero_telephone'],
            mail=data['mail'],
            acte=data['acte'],
            modalite_paiement=data['modalite_paiement'],
            paiement=mapping_paiement.get(data['acte'], 0),  # Valeur par défaut à 0 si la clé n'est pas présente
            observation=data['observation'],
            paiement_cps=mapping_paiement_cps.get(data['acte'], 0)  # Valeur par défaut à 0 si la clé n'est pas présente
        )

    db.session.add(nouvelle_activite)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    activite = Activite.query.get(id)
    if request.method == 'POST':
        # Mettez à jour les données de l'activité
        activite.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        activite.numero_semaine = request.form['numero_semaine']
        activite.numero_facture = request.form['numero_facture']
        activite.dn = request.form['dn']
        activite.nom = request.form['nom']
        activite.prenom = request.form['prenom']
        activite.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        activite.numero_telephone=request.form['numero_telephone']
        activite.mail=request.form['mail']
        activite.acte = request.form['acte']
        activite.modalite_paiement = request.form['modalite_paiement']
        activite.paiement = request.form['paiement']
        activite.observation = request.form['observation']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('modifier.html', activite=activite)

@app.route('/supprimer/<int:id>')
def supprimer(id):
    activite = Activite.query.get(id)
    db.session.delete(activite)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/exporter-excel')
def exporter_excel():
    activites = Activite.query.all()
    df = pd.DataFrame([a.__dict__ for a in activites])
    df.to_excel('activites.xlsx', index=False)
    return redirect(url_for('index'))

# Nouvelle route pour le bordereau
@app.route('/bordereau', methods=['GET', 'POST'])
@login_required
def bordereau():
    numero_bordereau = request.form.get('numero_bordereau', '')
    date_bordereau = request.form.get('date_bordereau', '')

    if request.method == 'POST':
        numero_semaine = request.form.get('numero_semaine')
        bordereau_data = Activite.query.filter_by(numero_semaine=numero_semaine).all()
    else:
        bordereau_data = []
    
    return render_template('bordereau.html', bordereau_data=bordereau_data, format_date=format_date)
    # return render_template('bordereau.html', bordereau_data=bordereau_data, numero_bordereau=numero_bordereau, date_bordereau=date_bordereau)

# Fonction pour formater les dates en français
def format_date(date):
    return date.strftime('%d/%m/%Y')

@app.route('/tableau_synthese', methods=['GET'])
@login_required
def tableau_synthese():
    # Agrégation par numéro de semaine et par acte
    result = db.session.query(
        Activite.numero_semaine,
        Activite.acte,
        func.sum(Activite.paiement).label('somme_paiement'),
        func.count().label('nombre_actes')
    ).group_by(Activite.numero_semaine, Activite.acte).all()

    # Structurez les résultats pour faciliter l'affichage dans le modèle
    tableau_synthese = {}
    for semaine, acte, somme_paiement, nombre_actes in result:
        if semaine not in tableau_synthese:
            tableau_synthese[semaine] = []
        tableau_synthese[semaine].append({
            'acte': acte,
            'somme_paiement': somme_paiement,
            'nombre_actes': nombre_actes
        })

    return render_template('tableau_synthese.html', tableau_synthese=tableau_synthese)

# Dictionnaire des correspondances actes-variables
correspondances_actes = {
    'CS': {'montant_paye': 4600, 'quote_part_patient': 4600, 'quote_part_organisme': 0},
    'ZCQM005': {'montant_paye': 4573, 'quote_part_patient': 4573, 'quote_part_organisme': 10672},
    # Ajoutez d'autres actes au besoin
}

@app.route('/generer-facture/<int:id>')
def generer_facture(id):
    activite = Activite.query.get(id)

    # Obtenez la date actuelle
    date_du_jour = datetime.now().strftime('%d/%m/%Y')

    # Récupérez les détails de la facture (ajustez selon vos besoins)
    details_facture = [
        {
            'acte': activite.acte,
            'date': activite.date,
            'nom': activite.nom,
            'prenom': activite.prenom,
            'dn': activite.dn,
            'modalite_paiement': activite.modalite_paiement,
            'paiement': activite.paiement
        }
    # Ajoutez d'autres détails au besoin
    ]

    # Calculez le total (ajustez selon vos besoins)
    total = sum(entry['paiement'] for entry in details_facture)

    # Récupérer les correspondances variables pour l'acte spécifique
    variables_acte = correspondances_actes.get(activite.acte, {})

    return render_template('facture.html', date_du_jour=date_du_jour, variables_acte=variables_acte, date=activite.date, numero_facture=activite.numero_facture, details=details_facture, total=total)

@app.route('/facture/<int:id>')
def facture(id):
    # Utilisez le paramètre id pour récupérer l'URL de la facture
    url_facture = url_for('generer_facture', id=id)
    return redirect(url_facture)  # Redirigez vers l'URL générée pour la facture

@app.route('/rechercher', methods=['GET', 'POST'])
@login_required
def rechercher():
    if request.method == 'POST':
        terme_recherche = request.form['terme_recherche']

        # Recherche par nom, date, ou acte
        results = Activite.query.filter(
            (Activite.nom.like(f'%{terme_recherche}%')) |
            (Activite.date.like(f'%{terme_recherche}%')) |
            (Activite.acte.like(f'%{terme_recherche}%'))
        ).all()

        return render_template('resultats_recherche.html', results=results, terme_recherche=terme_recherche, format_date=format_date)

    return render_template('rechercher.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            #print('user')
            flash('Connecté avec succès!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Échec de la connexion. Veuillez vérifier vos identifiants.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

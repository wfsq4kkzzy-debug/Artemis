from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, IntegerField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from models import UctovaSkupina, RozpoctovaPolozka

class NovaRozpoctovaPolozkaBez(FlaskForm):
    """Formulář pro přidání nové rozpočtové položky bez automatického výběru účtu"""
    uctova_skupina = SelectField('Účtová skupina', coerce=int, validators=[DataRequired()])
    analyticky_ucet = StringField('Analytický účet', validators=[DataRequired(), Length(min=1, max=10)])
    nazev = StringField('Název položky', validators=[DataRequired(), Length(min=3, max=300)])
    rozpocet = DecimalField('Rozpočet (Kč)', validators=[DataRequired(), NumberRange(min=0)])
    poznamka = TextAreaField('Poznámka', validators=[Optional()])
    submit = SubmitField('Přidat položku')
    
    def __init__(self, *args, **kwargs):
        super(NovaRozpoctovaPolozkaBez, self).__init__(*args, **kwargs)
        self.uctova_skupina.choices = [
            (ug.id, f'{ug.ucet} - {ug.nazev}')
            for ug in UctovaSkupina.query.order_by(UctovaSkupina.ucet).all()
        ]


class UpravitRozpocetPolozkuForm(FlaskForm):
    """Formulář pro úpravu rozpočtové položky"""
    nazev = StringField('Název položky', validators=[DataRequired(), Length(min=3, max=300)])
    rozpocet = DecimalField('Rozpočet (Kč)', validators=[DataRequired(), NumberRange(min=0)])
    poznamka = TextAreaField('Poznámka', validators=[Optional()])
    submit = SubmitField('Uložit změny')


class PridatVydajForm(FlaskForm):
    """Formulář pro přidání výdaje"""
    castka = DecimalField('Částka (Kč)', validators=[DataRequired(), NumberRange(min=0)])
    popis = StringField('Popis', validators=[Optional(), Length(max=300)])
    cis_faktury = StringField('Číslo faktury', validators=[Optional(), Length(max=50)])
    dodavatel = StringField('Dodavatel', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Přidat výdaj')


class FilterForm(FlaskForm):
    """Formulář pro filtrování rozpočtových položek"""
    uctova_skupina = SelectField('Účtová skupina', coerce=int, validators=[Optional()])
    typ = SelectField('Typ', choices=[('', '-- Všechno --'), ('naklad', 'Náklady'), ('vynos', 'Výnosy')], validators=[Optional()])
    submit = SubmitField('Filtrovat')
    
    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.uctova_skupina.choices = [
            (0, '-- Všechny --'),
        ] + [
            (ug.id, f'{ug.ucet} - {ug.nazev}')
            for ug in UctovaSkupina.query.order_by(UctovaSkupina.ucet).all()
        ]


class PridatZamestnanceForm(FlaskForm):
    """Formulář pro přidání zaměstnance nebo OON"""
    jmeno = StringField('Jméno', validators=[DataRequired(), Length(min=2, max=100)])
    prijmeni = StringField('Příjmení', validators=[DataRequired(), Length(min=2, max=100)])
    typ = SelectField('Typ', choices=[
        ('zamestnanec', 'Zaměstnanec'),
        ('brigadnik', 'Brigádník'),
        ('oon', 'OON (Osoba zvučující OON)')
    ], validators=[DataRequired()])
    ic_dph = StringField('IČ/DIČ (pro OON)', validators=[Optional(), Length(max=20)])
    pozice = StringField('Pozice', validators=[Optional(), Length(max=100)])
    uvazek = DecimalField('Úvazek (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=100)
    mesicni_plat = DecimalField('Měsíční plat (Kč)', validators=[Optional(), NumberRange(min=0)])
    hodinova_sazba = DecimalField('Hodinová sazba (Kč)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Přidat')

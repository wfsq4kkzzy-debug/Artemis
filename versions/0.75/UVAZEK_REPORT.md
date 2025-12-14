# ✅ Opravy a vylepšení - Úpravy zaměstnanců

## 🔧 Nová funkce: Pole "Úvazek"

### 1. ✅ Přidáno pole `uvazek` (velikost úvazku)

**Co bylo změněno:**

#### models.py
- Nový sloupec: `uvazek = db.Column(db.Numeric(5, 2), nullable=True, default=100)`
- Hodnota v procentech: 0-100% (100% = plný úvazek)

#### forms.py
```python
uvazek = DecimalField('Úvazek (%)', 
    validators=[Optional(), NumberRange(min=0, max=100)], 
    default=100)
```

#### app.py
- Přidáno ukládání úvazku v `pridat_cloveka()`
- Přidáno prefillování úvazku v `upravit_cloveka()`

#### Templates
- Přidáno pole v `personalni/pridat.html`
- Přidáno pole v `personalni/upravit.html`
- Zobrazení úvazku v `personalni/seznam.html`

---

## 🎨 Oprava: Fixní výška karet zaměstnanců

### Co bylo problém:
Každá nová osoba měla různou velikost karty v závislosti na obsahu

### Řešení:
Přidána Bootstrap třída `h-100` na `.card` element:

```html
<div class="card h-100">
    <div class="card-body d-flex flex-column">
        <!-- obsah -->
        <div class="card-footer mt-auto">
            <!-- tlačítka -->
        </div>
    </div>
</div>
```

**Co to dělá:**
- `h-100` - karta má fixní výšku 100% kontejneru (všechny karty v řádku stejné)
- `d-flex flex-column` - obsah je seřazen do sloupce
- `mt-auto` - footer se vždy posunuje na konec karty

---

## 📋 UI Vylepšení

### Formulář pro přidání/úpravu zaměstnance
Nové pole se vstupem:
```html
<div class="mb-3">
    <label>Úvazek (%)</label>
    <div class="input-group">
        <input type="number" class="form-control" placeholder="100" step="0.5" min="0" max="100">
        <span class="input-group-text">%</span>
    </div>
    <small class="form-text text-muted">0-100% (100% = plný úvazek)</small>
</div>
```

### Seznam zaměstnanců
- ✅ Všechny karty mají stejnou výšku (fixní)
- ✅ Tlačítko "Upravit" je vždy na dnu
- ✅ Zobrazení úvazku vedle pozice
- ✅ Přehledný layout

---

## 🧪 Testované funkce

| Operace | Status | Poznámka |
|---------|--------|----------|
| Přidání zaměstnance s úvazkem | ✅ | Úvazek se uloží jako výchozí 100% |
| Úprava zaměstnance | ✅ | Úvazek se prefilluje a dá se změnit |
| Zobrazení v seznamu | ✅ | Úvazek se zobrazuje v kartě |
| Fixní výška karet | ✅ | Všechny karty stejně vysoké |
| Responsivní design | ✅ | Karty se přizpůsobují šířce obrazovky |

---

## 📊 Databázové změny

### Migrate z staré databáze
```bash
rm -f library_budget.db
python3 init_db.py
```

**Nový schéma zaměstnance:**
```sql
CREATE TABLE zamestnanec_oon (
    id INTEGER PRIMARY KEY,
    jmeno VARCHAR(100) NOT NULL,
    prijmeni VARCHAR(100) NOT NULL,
    typ VARCHAR(20) NOT NULL,
    ic_dph VARCHAR(20),
    pozice VARCHAR(100),
    uvazek NUMERIC(5, 2) DEFAULT 100,
    hodinova_sazba NUMERIC(10, 2),
    mesicni_plat NUMERIC(12, 2),
    datum_zapojeni DATETIME DEFAULT CURRENT_TIMESTAMP,
    datum_ukonceni DATETIME,
    aktivni BOOLEAN DEFAULT TRUE
)
```

---

## 🚀 Nové možnosti

✅ Zadat velikost úvazku (0-100%)  
✅ Jednoduché přepočty (např. 50% úvazek = polovina platu)  
✅ Lepší vizuální srovnání zaměstnanců  
✅ Konzistentní layout bez "skákajících" prvků  

---

## 💡 Příklady verwendití

**Zaměstnanec na 75% úvazek:**
- Úvazek: 75%
- Měsíční plat: 30,000 Kč
- Efektivní plat: 22,500 Kč (75% z 30,000)

**Brigádník na 50% úvazek:**
- Úvazek: 50%
- Hodinová sazba: 200 Kč
- Týdenní fond: 20 hodin (50% ze 40)

---

**Poslední aktualizace**: 2025-12-09 18:12 CET  
**Status**: ✅ Všechny funkce opraveny a testovány

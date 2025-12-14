# Návrh modulu Uživatelé

## Požadavky

1. **Workspace pro každého uživatele** - každý uživatel má svůj workspace
2. **Propojení mezi uživateli** - možnost propojovat uživatele
3. **Sdílení informací z chatu** - sdílení AI chatů mezi uživateli
4. **Veřejné (transparentní)** - zatím vše veřejné
5. **Přidávání do projektů** - uživatelé mohou být přiřazeni k projektům
6. **Komunikace mezi uživateli** - zprávy, notifikace
7. **Propojení s personálním modulem** - každý uživatel pochází z personální databáze
8. **Admin práva** - admin může zadávat osoby do personálního modulu
9. **Efektivní interakce s ostatními moduly**

## Databázová struktura

### User (Uživatel)
- `id` - primární klíč
- `personnel_id` - FK na ZamestnanecAOON (povinné - každý uživatel pochází z personálního modulu)
- `username` - uživatelské jméno (unique)
- `email` - email (unique)
- `password_hash` - hash hesla (pro budoucí autentizaci)
- `role` - role ('admin', 'user', 'viewer')
- `aktivni` - je uživatel aktivní
- `workspace_settings` - JSON s nastavením workspace
- `datum_vytvoreni`, `datum_aktualizace`
- `posledni_prihlaseni` - poslední přihlášení

### UserProject (Uživatel v projektu)
- `id` - primární klíč
- `user_id` - FK na User
- `projekt_id` - FK na Projekt
- `role` - role v projektu ('owner', 'manager', 'member', 'viewer')
- `datum_pridani` - datum přidání do projektu
- `aktivni` - je přiřazení aktivní

### UserConnection (Propojení uživatelů)
- `id` - primární klíč
- `user1_id` - FK na User (první uživatel)
- `user2_id` - FK na User (druhý uživatel)
- `typ` - typ propojení ('colleague', 'supervisor', 'subordinate', 'custom')
- `aktivni` - je propojení aktivní
- `datum_vytvoreni`

### SharedChat (Sdílený chat)
- `id` - primární klíč
- `ai_session_id` - FK na AISession (z AI modulu)
- `shared_by_user_id` - FK na User (kdo sdílel)
- `shared_with_user_id` - FK na User (s kým je sdíleno, null = veřejné)
- `datum_sdileni` - datum sdílení
- `poznamka` - poznámka k sdílení

### UserMessage (Zpráva mezi uživateli)
- `id` - primární klíč
- `from_user_id` - FK na User (od koho)
- `to_user_id` - FK na User (komu, null = všem/veřejné)
- `subject` - předmět
- `content` - obsah zprávy
- `typ` - typ zprávy ('message', 'notification', 'system')
- `precteno` - je zpráva přečtena
- `datum_odeslani` - datum odeslání
- `datum_precteni` - datum přečtení

### UserNotification (Notifikace)
- `id` - primární klíč
- `user_id` - FK na User
- `typ` - typ notifikace ('project_update', 'message', 'task_assigned', 'budget_alert')
- `title` - nadpis
- `content` - obsah
- `precteno` - je přečtena
- `datum_vytvoreni`
- `related_id` - ID souvisejícího záznamu (projekt, zpráva, atd.)
- `related_type` - typ souvisejícího záznamu

## Propojení s moduly

### Personální modul
- **User.personnel_id** → **ZamestnanecAOON.id**
- Každý uživatel musí mít odpovídající záznam v personálním modulu
- Admin může vytvářet osoby v personálním modulu
- Při vytvoření uživatele se automaticky propojí s personálním záznamem

### Projekty
- **UserProject** propojuje **User** a **Projekt**
- Uživatelé mohou mít různé role v projektech
- V projektu může být více uživatelů
- Uživatel může být v více projektech

### AI modul
- **SharedChat** propojuje **AISession** a **User**
- Uživatelé mohou sdílet AI chaty
- Veřejné sdílení (shared_with_user_id = null)
- Sdílení s konkrétním uživatelem

### Rozpočet
- Uživatelé mohou vidět rozpočty (podle role)
- Admin může spravovat rozpočty
- Notifikace o překročení rozpočtu

## Workspace

### Workspace Settings (JSON)
```json
{
  "dashboard_layout": "default",
  "preferred_language": "cs",
  "notifications_enabled": true,
  "email_notifications": false,
  "theme": "light",
  "default_view": "dashboard",
  "filters": {
    "projects": [],
    "categories": []
  }
}
```

### Workspace Features
- Vlastní dashboard
- Filtrování projektů
- Vlastní zobrazení
- Nastavení notifikací

## Komunikace

### Zprávy
- Uživatelé si mohou posílat zprávy
- Veřejné zprávy (to_user_id = null)
- Privátní zprávy
- Systémové zprávy

### Notifikace
- Automatické notifikace při změnách v projektech
- Notifikace o nových zprávách
- Notifikace o přiřazení úkolů
- Notifikace o rozpočtu

## Role a oprávnění

### Admin
- Vytváření a úprava osob v personálním modulu
- Správa uživatelů
- Přístup ke všem projektům
- Správa rozpočtů

### User
- Vlastní workspace
- Účast v projektech (podle role v projektu)
- Sdílení chatů
- Komunikace s ostatními

### Viewer
- Pouze prohlížení
- Žádné úpravy

## Implementace

### Fáze 1: Základní struktura
- Modely User, UserProject, UserConnection
- Propojení s personálním modulem
- Základní routes

### Fáze 2: Workspace
- Workspace settings
- Dashboard pro uživatele
- Filtrování

### Fáze 3: Komunikace
- Zprávy mezi uživateli
- Notifikace
- Sdílení chatů

### Fáze 4: Pokročilé funkce
- Role v projektech
- Propojení uživatelů
- Veřejné/privátní sdílení





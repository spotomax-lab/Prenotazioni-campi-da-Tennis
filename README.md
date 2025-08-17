
# 🎾 Prenotazione Campi Tennis (PWA + Flask)

Un'app web responsive e installabile come app su smartphone per prenotare 2 campi da tennis con durate di **1h / 1h30 / 2h**.

## Funzionalità
- Vista giornaliera con fasce orarie a step di 30 min
- Prenotazione con nome, contatto (opz.) e nota
- Verifica conflitti in tempo reale
- Codice di annullamento e cancellazione self-service
- Area admin (password) + export JSON
- PWA: aggiungibile alla schermata Home su iOS/Android
- Configurabile via variabili d'ambiente (orari, campi, timezone)

## Avvio rapido (senza Docker)
1. **Scarica lo zip** di questo progetto e scompattalo
2. Installazione dipendenze
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **(Opzionale)** imposta le variabili d'ambiente
   ```bash
   export APP_TZ=Europe/Rome
   export OPEN_TIME=08:00
   export CLOSE_TIME=22:00
   export ADMIN_PASSWORD=una_password_sicura
   export COURTS="Campo 1,Campo 2"
   ```
4. **Esegui**
   ```bash
   python app.py
   ```
   L'app sarà su `http://localhost:8000`

## Avvio con Docker
```
docker build -t tennis-booking .
docker run -p 8000:8000 -e ADMIN_PASSWORD=una_password_sicura tennis-booking
```

## Note operative
- Gli orari sono valutati in timezone `APP_TZ` (default Europe/Rome)
- I dati sono salvati in `booking.db` (SQLite) nella cartella dell'app
- Per azzerare il db: eliminare `booking.db` a server spento
- Le durate consentite sono fisse a 60/90/120 min (modificabile da `app.py`)

## Sicurezza & privacy
- Non c'è login utenti: semplifica l'accesso per gli associati. Se volete il login (OTP, email, ecc.) posso aggiungerlo.
- Impostare sempre `ADMIN_PASSWORD` a un valore robusto.
- Se esponete su internet, usate un reverse proxy con HTTPS (Nginx, Caddy, Traefik).

## Personalizzazioni rapide
- **Nomi campi:** variabile `COURTS="Campo A,Campo B,Campo C"`
- **Fasce orarie:** `OPEN_TIME` e `CLOSE_TIME` (formato HH:MM)
- **Regole aggiuntive:** in `api_book()` potete aggiungere limiti (es. max 2h/giorno per persona).

Buon tennis! 🎾

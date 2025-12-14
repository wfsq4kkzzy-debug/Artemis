"""
Skript pro rychlé spuštění aplikace ve vývojovém režimu

Příklady:
    $ python dev.py              # Normální start
    $ python dev.py --host 0.0.0.0  # Dostupné na síti
"""

import os
import sys
import json
from datetime import datetime

# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"dev.py:11","message":"Starting app import","data":{"timestamp":datetime.now().isoformat()},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
# #endregion

from app import app, db
from models import UctovaSkupina, RozpoctovaPolozka, Vydaj, ZamestnanecAOON

# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"dev.py:15","message":"App imported successfully","data":{"blueprints":list(app.blueprints.keys()) if hasattr(app,'blueprints') else []},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
# #endregion

def create_app():
    """Vytvoří a nastaví aplikaci"""
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"dev.py:19","message":"create_app called","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
    # #endregion
    
    with app.app_context():
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"dev.py:22","message":"Before db.create_all","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # Vytvoří tabulky, pokud neexistují
        try:
            db.create_all()
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"dev.py:26","message":"db.create_all completed","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
            # #endregion
        except Exception as e:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"dev.py:29","message":"db.create_all failed","data":{"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
            # #endregion
            raise
        
        # Zkontroluje, zda je databáze prázdná
        if UctovaSkupina.query.count() == 0:
            print("⚠️  Databáze je prázdná. Spusťte: python init_db.py")
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"dev.py:35","message":"create_app returning","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
        # #endregion
        
        return app

if __name__ == '__main__':
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"dev.py:40","message":"Main block entered","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
    # #endregion
    
    try:
        app = create_app()
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"dev.py:45","message":"App created, before app.run","data":{},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
        # #endregion
        
        print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║   📚 Správa rozpočtu Městské knihovny Polička                  ║
    ║                                                                ║
    ║   🌐 http://127.0.0.1:5001                                    ║
    ║   🐍 Python 3.8+                                              ║
    ║   💾 SQLite                                                   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"dev.py:58","message":"Before app.run","data":{"host":"127.0.0.1","port":5000},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
        # #endregion
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5001,
            use_reloader=True
        )
    except Exception as e:
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"dev.py:67","message":"Exception in main","data":{"error":str(e),"type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)})+'\n')
        # #endregion
        raise

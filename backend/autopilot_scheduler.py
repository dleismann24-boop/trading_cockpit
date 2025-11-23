"""
Autopilot Scheduler - Automatische Trading-Zyklen
Führt regelmäßig Trading-Zyklen aus basierend auf der Konfiguration
"""
import logging
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class AutopilotScheduler:
    """Verwaltet automatische Trading-Zyklen"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='US/Eastern')
        self.job_id = 'autopilot_trading_cycle'
        self.trading_controller = None
        self.trading_client = None
        self.is_running = False
        
        # Start scheduler
        self.scheduler.start()
        logger.info("🤖 Autopilot Scheduler initialisiert")
    
    def set_trading_controller(self, controller):
        """Setzt den Trading Controller"""
        self.trading_controller = controller
        logger.info("Trading Controller für Autopilot gesetzt")
    
    def set_trading_client(self, client):
        """Setzt den Trading Client für Markt-Check"""
        self.trading_client = client
    
    def is_market_open(self) -> bool:
        """Prüft ob Markt aktuell offen ist"""
        try:
            if self.trading_client:
                clock = self.trading_client.get_clock()
                return clock.is_open
            else:
                # Fallback: Check Wochentag und Uhrzeit
                now = datetime.now()
                is_weekday = now.weekday() < 5  # Mo-Fr
                current_time = now.time()
                market_open = time(9, 30)
                market_close = time(16, 0)
                return is_weekday and market_open <= current_time <= market_close
        except Exception as e:
            logger.error(f"Fehler beim Markt-Check: {e}")
            return False
    
    def run_trading_cycle_sync(self):
        """Führt Trading-Zyklus aus (Wrapper für async)"""
        try:
            # Markt-Check
            if not self.is_market_open():
                logger.info("⏸️  Autopilot: Markt ist geschlossen - überspringe Zyklus")
                return
            
            if not self.trading_controller:
                logger.error("Trading Controller nicht gesetzt!")
                return
            
            logger.info("🚀 Autopilot: Starte automatischen Trading-Zyklus...")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self.trading_controller.run_trading_cycle()
            )
            loop.close()
            
            logger.info(f"✅ Autopilot: Zyklus abgeschlossen - {results['trades_executed']} Trades")
            
        except Exception as e:
            logger.error(f"❌ Autopilot-Fehler: {e}", exc_info=True)
    
    def start_autopilot(self, interval_minutes: int):
        """Startet den Autopilot mit gegebenem Intervall"""
        try:
            # Entferne alten Job falls vorhanden
            self.stop_autopilot()
            
            # Erstelle neuen Job
            trigger = IntervalTrigger(minutes=interval_minutes, timezone='US/Eastern')
            
            self.scheduler.add_job(
                func=self.run_trading_cycle_sync,
                trigger=trigger,
                id=self.job_id,
                name='Autopilot Trading Cycle',
                replace_existing=True
            )
            
            self.is_running = True
            logger.info(f"✅ Autopilot gestartet - Intervall: {interval_minutes} Minuten")
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Autopilots: {e}")
            return False
    
    def stop_autopilot(self):
        """Stoppt den Autopilot"""
        try:
            if self.scheduler.get_job(self.job_id):
                self.scheduler.remove_job(self.job_id)
                logger.info("⏸️  Autopilot gestoppt")
            
            self.is_running = False
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des Autopilots: {e}")
            return False
    
    def get_next_run(self) -> Optional[datetime]:
        """Gibt die nächste geplante Ausführung zurück"""
        try:
            job = self.scheduler.get_job(self.job_id)
            if job:
                return job.next_run_time
            return None
        except:
            return None
    
    def get_status(self) -> dict:
        """Status des Schedulers"""
        job = self.scheduler.get_job(self.job_id)
        
        return {
            'is_running': self.is_running,
            'has_job': job is not None,
            'next_run': str(job.next_run_time) if job else None,
            'scheduler_running': self.scheduler.running
        }
    
    def shutdown(self):
        """Fährt den Scheduler herunter"""
        logger.info("Shutting down Autopilot Scheduler...")
        self.scheduler.shutdown(wait=False)


# Global Scheduler Instance
_scheduler_instance = None

def get_autopilot_scheduler() -> AutopilotScheduler:
    """Get or create global autopilot scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutopilotScheduler()
    return _scheduler_instance

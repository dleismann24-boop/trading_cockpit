import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export default function Agenten() {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [cycleRunning, setCycleRunning] = useState(false);
  
  // Autopilot State
  const [autopilotEnabled, setAutopilotEnabled] = useState(false);
  const [autopilotInterval, setAutopilotInterval] = useState(60);
  const [autopilotConfig, setAutopilotConfig] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try:
      const [statusRes, leaderboardRes, autopilotRes] = await Promise.all([
        axios.get(`${API_URL}/api/autonomous/status`),
        axios.get(`${API_URL}/api/autonomous/leaderboard`),
        axios.get(`${API_URL}/api/autonomous/autopilot/status`),
      ]);

      if (statusRes.data.success) {
        setStatus(statusRes.data.status);
      }

      if (leaderboardRes.data.success) {
        setLeaderboard(leaderboardRes.data.leaderboard);
      }

      if (autopilotRes.data.success) {
        setAutopilotConfig(autopilotRes.data.config);
        setAutopilotEnabled(autopilotRes.data.config.enabled);
        setAutopilotInterval(autopilotRes.data.config.interval_minutes);
      }
    } catch (error) {
      console.error('Error loading agent data:', error);
    }
  };

  const toggleAutopilot = async (enabled: boolean) => {
    try {
      const response = await axios.post(`${API_URL}/api/autonomous/autopilot/configure`, {
        enabled,
        interval_minutes: autopilotInterval,
      });

      if (response.data.success) {
        setAutopilotEnabled(enabled);
        setAutopilotConfig(response.data.config);
        alert(enabled ? 'Autopilot aktiviert!' : 'Autopilot deaktiviert');
        await loadData();
      }
    } catch (error) {
      console.error('Autopilot toggle error:', error);
      alert('Fehler beim Umschalten des Autopilots');
    }
  };

  const updateInterval = async (minutes: number) => {
    setAutopilotInterval(minutes);
    
    if (autopilotEnabled) {
      try {
        await axios.post(`${API_URL}/api/autonomous/autopilot/configure`, {
          enabled: true,
          interval_minutes: minutes,
        });
      } catch (error) {
        console.error('Interval update error:', error);
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const startTradingCycle = async () => {
    setCycleRunning(true);
    try {
      const response = await axios.post(`${API_URL}/api/autonomous/start-cycle`);
      
      if (response.data.success) {
        alert(`Trading-Zyklus abgeschlossen!\n${response.data.results.trades_executed} Trades ausgeführt`);
        await loadData();
      }
    } catch (error) {
      console.error('Trading cycle error:', error);
      alert('Fehler beim Trading-Zyklus');
    } finally {
      setCycleRunning(false);
    }
  };

  const getAgentIcon = (agentName: string) => {
    switch (agentName.toLowerCase()) {
      case 'jordan': return '🏀';
      case 'bohlen': return '🎤';
      case 'frodo': return '🧙';
      default: return '🤖';
    }
  };

  const getAgentColor = (rank: number) => {
    switch (rank) {
      case 1: return '#FFD700'; // Gold
      case 2: return '#C0C0C0'; // Silber
      case 3: return '#CD7F32'; // Bronze
      default: return '#666';
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Autonome Agenten</Text>
          <Text style={styles.headerSubtitle}>
            Modus: {status?.mode || 'Solo'}
          </Text>
        </View>
        <MaterialCommunityIcons name="robot" size={32} color="#10b981" />
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#f97316" />
        }
      >
        {/* Start Trading Cycle Button */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.startButton, cycleRunning && styles.startButtonDisabled]}
            onPress={startTradingCycle}
            disabled={cycleRunning}
          >
            {cycleRunning ? (
              <>
                <ActivityIndicator color="#fff" />
                <Text style={styles.startButtonText}>Trading läuft...</Text>
              </>
            ) : (
              <>
                <MaterialCommunityIcons name="play-circle" size={24} color="#fff" />
                <Text style={styles.startButtonText}>Trading-Zyklus starten</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Leaderboard */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Leaderboard</Text>
          
          {leaderboard.map((agent, index) => (
            <View key={index} style={styles.leaderboardCard}>
              <View style={styles.leaderboardHeader}>
                <View style={styles.agentInfo}>
                  <Text style={styles.agentIcon}>{getAgentIcon(agent.agent)}</Text>
                  <View>
                    <Text style={styles.agentName}>{agent.agent}</Text>
                    <Text style={styles.agentRank}>Rang #{agent.rank}</Text>
                  </View>
                </View>
                <View style={[styles.rankBadge, { backgroundColor: getAgentColor(agent.rank) }]}>
                  <Text style={styles.rankText}>{agent.rank}</Text>
                </View>
              </View>

              <View style={styles.statsGrid}>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>Trades</Text>
                  <Text style={styles.statValue}>{agent.total_trades}</Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>Erfolgsrate</Text>
                  <Text style={styles.statValue}>
                    {(agent.success_rate * 100).toFixed(0)}%
                  </Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>P&L</Text>
                  <Text
                    style={[
                      styles.statValue,
                      { color: agent.total_pnl >= 0 ? '#10b981' : '#ef4444' },
                    ]}
                  >
                    ${agent.total_pnl.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>
          ))}

          {leaderboard.length === 0 && (
            <View style={styles.emptyState}>
              <MaterialCommunityIcons name="trophy-outline" size={48} color="#666" />
              <Text style={styles.emptyText}>Noch keine Daten</Text>
              <Text style={styles.emptySubtext}>Starte den ersten Trading-Zyklus</Text>
            </View>
          )}
        </View>

        {/* Agent Status Details */}
        {status?.agents_status && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Agent-Details</Text>

            {Object.entries(status.agents_status).map(([name, stats]: [string, any]) => (
              <View key={name} style={styles.agentDetailCard}>
                <View style={styles.agentDetailHeader}>
                  <Text style={styles.agentDetailIcon}>{getAgentIcon(name)}</Text>
                  <Text style={styles.agentDetailName}>{name}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Gesamt Trades:</Text>
                  <Text style={styles.detailValue}>{stats.total_trades}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Nachrichten:</Text>
                  <Text style={styles.detailValue}>{stats.message_count}</Text>
                </View>

                {stats.recent_trades && stats.recent_trades.length > 0 && (
                  <View style={styles.recentTrades}>
                    <Text style={styles.recentTradesTitle}>Letzte Trades:</Text>
                    {stats.recent_trades.slice(0, 3).map((trade: any, i: number) => (
                      <View key={i} style={styles.tradeItem}>
                        <Text style={styles.tradeSymbol}>{trade.symbol}</Text>
                        <Text
                          style={[
                            styles.tradeAction,
                            { color: trade.action === 'BUY' ? '#10b981' : '#ef4444' },
                          ]}
                        >
                          {trade.action} {trade.quantity}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            ))}
          </View>
        )}

        {/* System Info */}
        {status && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>System-Info</Text>
            <View style={styles.infoCard}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Modus:</Text>
                <Text style={styles.infoValue}>{status.mode}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Watchlist:</Text>
                <Text style={styles.infoValue}>
                  {status.watchlist?.join(', ') || 'Keine'}
                </Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Letzter Lauf:</Text>
                <Text style={styles.infoValue}>
                  {status.last_run
                    ? new Date(status.last_run).toLocaleString('de-DE')
                    : 'Noch nicht gelaufen'}
                </Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 10,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#10b981',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
    paddingTop: 0,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
    marginTop: 20,
  },
  startButton: {
    flexDirection: 'row',
    backgroundColor: '#10b981',
    padding: 18,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    marginTop: 20,
  },
  startButtonDisabled: {
    backgroundColor: '#666',
  },
  startButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  leaderboardCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  leaderboardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  agentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  agentIcon: {
    fontSize: 32,
  },
  agentName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    textTransform: 'capitalize',
  },
  agentRank: {
    fontSize: 12,
    color: '#888',
  },
  rankBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  rankText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#0a0a0a',
    padding: 12,
    borderRadius: 8,
  },
  statLabel: {
    fontSize: 11,
    color: '#888',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#444',
    marginTop: 4,
  },
  agentDetailCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  agentDetailHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  agentDetailIcon: {
    fontSize: 24,
  },
  agentDetailName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    textTransform: 'capitalize',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#888',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  recentTrades: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#2a2a2a',
  },
  recentTradesTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#888',
    marginBottom: 8,
  },
  tradeItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  tradeSymbol: {
    fontSize: 13,
    color: '#ccc',
  },
  tradeAction: {
    fontSize: 13,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 14,
    color: '#888',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
    textAlign: 'right',
  },
});

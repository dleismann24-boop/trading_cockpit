import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

type Phase = 'start' | 'research' | 'discussion' | 'consensus' | 'done';

export default function AIZentrale() {
  const [phase, setPhase] = useState<Phase>('start');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [researchResults, setResearchResults] = useState<any>(null);
  const [discussionResults, setDiscussionResults] = useState<any>(null);
  const [consensusResult, setConsensusResult] = useState<any>(null);
  const [userInput, setUserInput] = useState('');

  const startResearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setPhase('research');
    
    // Mock für jetzt - später echte API
    setTimeout(() => {
      setResearchResults({
        jordan: "Apple (AAPL) ist stark! Ich würde jetzt 50 Aktien kaufen. Das Momentum ist da, lass uns gewinnen! 🏀",
        bohlen: "AAPL ist okay, aber überteuert. Wenn, dann maximal 20 Aktien. Nicht zu gierig werden!",
        frodo: "Apple ist solide für langfristig. 30 Aktien wären vernünftig. Geduld zahlt sich aus."
      });
      setLoading(false);
    }, 2000);
  };

  const startDiscussion = () => {
    setLoading(true);
    setPhase('discussion');
    
    setTimeout(() => {
      setDiscussionResults({
        jordan: "Ich bleibe dabei - 50 Aktien! Wer nicht wagt, der nicht gewinnt.",
        bohlen: "Jordan, du bist verrückt. 30 Aktien sind das Maximum. Frodo hat recht.",
        frodo: "Einigen wir uns auf 30-35 Aktien. Das ist der Mittelweg."
      });
      setLoading(false);
    }, 2000);
  };

  const generateConsensus = () => {
    setLoading(true);
    setPhase('consensus');
    
    setTimeout(() => {
      setConsensusResult({
        symbol: "AAPL",
        action: "KAUFEN",
        quantity: 32,
        reason: "Solide Firma, gutes Momentum, vernünftige Menge"
      });
      setLoading(false);
    }, 1500);
  };

  const executeTrade = () => {
    setLoading(true);
    setTimeout(() => {
      setPhase('done');
      setLoading(false);
    }, 1000);
  };

  const reset = () => {
    setPhase('start');
    setQuery('');
    setResearchResults(null);
    setDiscussionResults(null);
    setConsensusResult(null);
    setUserInput('');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>KI-Zentrale</Text>
        <Text style={styles.headerSubtitle}>
          Jordan • Bohlen • Frodo
        </Text>
      </View>

      {/* Phase Indicator */}
      <View style={styles.phaseIndicator}>
        <View style={[styles.phaseStep, phase !== 'start' && styles.phaseStepActive]}>
          <Text style={styles.phaseText}>1. Research</Text>
        </View>
        <View style={[styles.phaseStep, phase === 'discussion' || phase === 'consensus' || phase === 'done' ? styles.phaseStepActive : null]}>
          <Text style={styles.phaseText}>2. Diskussion</Text>
        </View>
        <View style={[styles.phaseStep, phase === 'consensus' || phase === 'done' ? styles.phaseStepActive : null]}>
          <Text style={styles.phaseText}>3. Konsens</Text>
        </View>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Phase: Start */}
        {phase === 'start' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Deep Research starten</Text>
            <Text style={styles.sectionDesc}>
              Die 3 KIs analysieren deine Frage und geben Empfehlungen
            </Text>
            
            <TextInput
              style={styles.input}
              placeholder="z.B. Soll ich Apple Aktien kaufen?"
              placeholderTextColor="#666"
              value={query}
              onChangeText={setQuery}
              multiline
            />
            
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={startResearch}
              disabled={!query.trim() || loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <MaterialCommunityIcons name="rocket-launch" size={24} color="#fff" />
                  <Text style={styles.buttonText}>Research starten</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Phase: Research Results */}
        {phase === 'research' && researchResults && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Research-Ergebnisse</Text>
            
            <View style={styles.aiCard}>
              <Text style={styles.aiName}>🏀 Jordan (GPT-4)</Text>
              <Text style={styles.aiResponse}>{researchResults.jordan}</Text>
            </View>
            
            <View style={styles.aiCard}>
              <Text style={styles.aiName}>🎤 Bohlen (Claude)</Text>
              <Text style={styles.aiResponse}>{researchResults.bohlen}</Text>
            </View>
            
            <View style={styles.aiCard}>
              <Text style={styles.aiName}>🧙 Frodo (Gemini)</Text>
              <Text style={styles.aiResponse}>{researchResults.frodo}</Text>
            </View>
            
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={startDiscussion}
            >
              <Text style={styles.buttonText}>Weiter zur Diskussion</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Phase: Discussion */}
        {phase === 'discussion' && discussionResults && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>KI-Diskussion</Text>
            <Text style={styles.sectionDesc}>Die KIs diskutieren untereinander</Text>
            
            <View style={styles.discussionThread}>
              {Object.entries(discussionResults).map(([key, value], i) => (
                <View key={i} style={styles.discussionBubble}>
                  <Text style={styles.discussionName}>
                    {key === 'jordan' ? '🏀 Jordan' : key === 'bohlen' ? '🎤 Bohlen' : '🧙 Frodo'}
                  </Text>
                  <Text style={styles.discussionText}>{value as string}</Text>
                </View>
              ))}
            </View>
            
            <TextInput
              style={styles.input}
              placeholder="Deine Meinung? (optional)"
              placeholderTextColor="#666"
              value={userInput}
              onChangeText={setUserInput}
            />
            
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={generateConsensus}
            >
              <Text style={styles.buttonText}>Konsens generieren</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Phase: Consensus */}
        {phase === 'consensus' && consensusResult && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Konsens-Empfehlung</Text>
            
            <View style={styles.consensusCard}>
              <View style={styles.consensusRow}>
                <Text style={styles.consensusLabel}>Symbol:</Text>
                <Text style={styles.consensusValue}>{consensusResult.symbol}</Text>
              </View>
              <View style={styles.consensusRow}>
                <Text style={styles.consensusLabel}>Aktion:</Text>
                <Text style={[styles.consensusValue, styles.consensusAction]}>
                  {consensusResult.action}
                </Text>
              </View>
              <View style={styles.consensusRow}>
                <Text style={styles.consensusLabel}>Menge:</Text>
                <Text style={styles.consensusValue}>{consensusResult.quantity} Aktien</Text>
              </View>
              <View style={styles.consensusRow}>
                <Text style={styles.consensusLabel}>Begründung:</Text>
                <Text style={styles.consensusReason}>{consensusResult.reason}</Text>
              </View>
            </View>
            
            <TouchableOpacity
              style={[styles.primaryButton, styles.executeButton]}
              onPress={executeTrade}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <MaterialCommunityIcons name="check-circle" size={24} color="#fff" />
                  <Text style={styles.buttonText}>Trade ausführen</Text>
                </>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={reset}
            >
              <Text style={styles.secondaryButtonText}>Abbrechen</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Phase: Done */}
        {phase === 'done' && (
          <View style={styles.section}>
            <View style={styles.successCard}>
              <MaterialCommunityIcons name="check-circle" size={64} color="#10b981" />
              <Text style={styles.successTitle}>Trade ausgeführt!</Text>
              <Text style={styles.successText}>
                {consensusResult.quantity} {consensusResult.symbol} Aktien wurden gekauft.
              </Text>
              
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={reset}
              >
                <Text style={styles.buttonText}>Neue Analyse starten</Text>
              </TouchableOpacity>
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
    padding: 20,
    paddingTop: 10,
    alignItems: 'center',
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
  phaseIndicator: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  phaseStep: {
    flex: 1,
    padding: 12,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  phaseStepActive: {
    backgroundColor: '#f97316',
    borderColor: '#f97316',
  },
  phaseText: {
    fontSize: 12,
    color: '#fff',
    textAlign: 'center',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  sectionDesc: {
    fontSize: 14,
    color: '#888',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    padding: 16,
    fontSize: 15,
    color: '#fff',
    minHeight: 80,
    marginBottom: 16,
  },
  primaryButton: {
    flexDirection: 'row',
    backgroundColor: '#f97316',
    padding: 16,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  secondaryButton: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#888',
  },
  aiCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  aiName: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#f97316',
    marginBottom: 8,
  },
  aiResponse: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  discussionThread: {
    marginBottom: 20,
  },
  discussionBubble: {
    backgroundColor: '#1a1a1a',
    padding: 14,
    borderRadius: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#10b981',
  },
  discussionName: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#10b981',
    marginBottom: 6,
  },
  discussionText: {
    fontSize: 14,
    color: '#ccc',
  },
  consensusCard: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderRadius: 16,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#10b981',
  },
  consensusRow: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'center',
  },
  consensusLabel: {
    fontSize: 14,
    color: '#888',
    width: 100,
  },
  consensusValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  consensusAction: {
    color: '#10b981',
  },
  consensusReason: {
    fontSize: 14,
    color: '#ccc',
    flex: 1,
  },
  executeButton: {
    backgroundColor: '#10b981',
  },
  successCard: {
    alignItems: 'center',
    padding: 40,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#10b981',
    marginTop: 16,
    marginBottom: 8,
  },
  successText: {
    fontSize: 15,
    color: '#ccc',
    textAlign: 'center',
    marginBottom: 32,
  },
});

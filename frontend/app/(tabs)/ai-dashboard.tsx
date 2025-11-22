import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  ImageBackground,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import { useTradingStore } from '../../store/tradingStore';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export default function AIDashboard() {
  const { account } = useTradingStore();
  const [autoPilotEnabled, setAutoPilotEnabled] = useState(false);
  const [researchQuery, setResearchQuery] = useState('');
  const [isResearching, setIsResearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [researchResults, setResearchResults] = useState<any>(null);
  const [autopilotResults, setAutopilotResults] = useState<any>(null);

  useEffect(() => {
    fetchAutopilotStatus();
  }, []);

  const fetchAutopilotStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/ai/autopilot/status`);
      setAutoPilotEnabled(response.data.enabled);
    } catch (error) {
      console.error('Error fetching autopilot status:', error);
    }
  };

  const toggleAutoPilot = async (value: boolean) => {
    try {
      await axios.post(`${API_URL}/api/ai/autopilot/toggle`, { enabled: value });
      setAutoPilotEnabled(value);
      if (value) {
        // Auto-run analysis when enabled
        runAutoPilotAnalysis();
      }
    } catch (error) {
      console.error('Error toggling autopilot:', error);
    }
  };

  const runDeepResearch = async () => {
    if (!researchQuery.trim()) return;

    setIsResearching(true);
    try {
      const response = await axios.post(`${API_URL}/api/ai/deep-research`, {
        query: researchQuery,
        symbols: [],
      });
      setResearchResults(response.data.research);
    } catch (error) {
      console.error('Deep research error:', error);
    } finally {
      setIsResearching(false);
    }
  };

  const runAutoPilotAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const response = await axios.post(`${API_URL}/api/ai/autopilot/analyze`);
      if (response.data.success) {
        setAutopilotResults(response.data.analysis);
      }
    } catch (error) {
      console.error('Autopilot analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <ImageBackground
      source={{ uri: 'https://images.unsplash.com/photo-1605514449459-5a9cfa0b9955?q=80&w=1200' }}
      style={styles.backgroundImage}
      imageStyle={{ opacity: 0.15 }}
    >
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>AI Command Center</Text>
            <Text style={styles.headerSubtitle}>Jordan • Bohlen • Frodo</Text>
          </View>
          <View style={styles.avatarContainer}>
            <MaterialCommunityIcons name="brain" size={32} color="#10b981" />
          </View>
        </View>

        <ScrollView style={styles.scrollView}>
          {/* Auto-Pilot Control */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <View>
                <Text style={styles.sectionTitle}>Auto-Pilot</Text>
                <Text style={styles.sectionSubtitle}>
                  Let the 3 AIs manage your portfolio
                </Text>
              </View>
              <Switch
                value={autoPilotEnabled}
                onValueChange={toggleAutoPilot}
                trackColor={{ false: '#2a2a2a', true: '#10b981' }}
                thumbColor={autoPilotEnabled ? '#fff' : '#666'}
              />
            </View>

            {autoPilotEnabled && (
              <View style={styles.autopilotCard}>
                <Text style={styles.autopilotStatus}>
                  🤖 Auto-Pilot Active
                </Text>
                <Text style={styles.autopilotLimit}>
                  Max trade size: 10% of portfolio ($
                  {account ? (account.portfolio_value * 0.1).toFixed(0) : '10,000'})
                </Text>
                <TouchableOpacity
                  style={styles.analyzeButton}
                  onPress={runAutoPilotAnalysis}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <>
                      <MaterialCommunityIcons name="radar" size={20} color="#fff" />
                      <Text style={styles.analyzeButtonText}>Run Analysis Now</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </View>

          {/* Auto-Pilot Results */}
          {autopilotResults && (
            <View style={styles.resultsCard}>
              <Text style={styles.resultsTitle}>Auto-Pilot Recommendation</Text>
              <View style={styles.consensusBar}>
                <View style={styles.consensusLabel}>
                  <Text style={styles.consensusText}>Consensus Strength</Text>
                  <Text style={styles.consensusValue}>
                    {(autopilotResults.consensus_strength * 100).toFixed(0)}%
                  </Text>
                </View>
                <View style={styles.consensusProgress}>
                  <View
                    style={[
                      styles.consensusFill,
                      {
                        width: `${autopilotResults.consensus_strength * 100}%`,
                        backgroundColor:
                          autopilotResults.consensus_strength > 0.6 ? '#10b981' : '#f97316',
                      },
                    ]}
                  />
                </View>
              </View>

              <View style={styles.aiOpinions}>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🏀 Jordan</Text>
                  <Text style={styles.aiResponse} numberOfLines={4}>
                    {autopilotResults.jordan}
                  </Text>
                </View>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🎤 Bohlen</Text>
                  <Text style={styles.aiResponse} numberOfLines={4}>
                    {autopilotResults.bohlen}
                  </Text>
                </View>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🧙 Frodo</Text>
                  <Text style={styles.aiResponse} numberOfLines={4}>
                    {autopilotResults.frodo}
                  </Text>
                </View>
              </View>
            </View>
          )}

          {/* Deep Research */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Deep Research</Text>
            <Text style={styles.sectionSubtitle}>
              Get all 3 AIs to analyze any market question
            </Text>

            <View style={styles.searchContainer}>
              <TextInput
                style={styles.searchInput}
                placeholder="Ask anything (e.g., 'Should I buy AAPL?')"
                placeholderTextColor="#666"
                value={researchQuery}
                onChangeText={setResearchQuery}
                multiline
              />
              <TouchableOpacity
                style={styles.researchButton}
                onPress={runDeepResearch}
                disabled={isResearching || !researchQuery.trim()}
              >
                {isResearching ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <MaterialCommunityIcons name="telescope" size={20} color="#fff" />
                    <Text style={styles.researchButtonText}>Research</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>

          {/* Research Results */}
          {researchResults && (
            <View style={styles.resultsCard}>
              <Text style={styles.resultsTitle}>Research Results</Text>
              <View style={styles.aiOpinions}>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🏀 Jordan (GPT-4)</Text>
                  <ScrollView style={styles.aiScrollView}>
                    <Text style={styles.aiResponse}>{researchResults.jordan}</Text>
                  </ScrollView>
                </View>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🎤 Bohlen (Claude)</Text>
                  <ScrollView style={styles.aiScrollView}>
                    <Text style={styles.aiResponse}>{researchResults.bohlen}</Text>
                  </ScrollView>
                </View>
                <View style={styles.aiOpinion}>
                  <Text style={styles.aiName}>🧙 Frodo (Gemini)</Text>
                  <ScrollView style={styles.aiScrollView}>
                    <Text style={styles.aiResponse}>{researchResults.frodo}</Text>
                  </ScrollView>
                </View>
              </View>
            </View>
          )}

          <View style={styles.disclaimer}>
            <MaterialCommunityIcons name=\"shield-alert\" size={16} color=\"#ef4444\" />
            <Text style={styles.disclaimerText}>
              AI suggestions are not financial advice. Always do your own research.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  backgroundImage: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 10,
    backgroundColor: 'rgba(10, 10, 10, 0.8)',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#10b981',
  },
  avatarContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#10b981',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#888',
  },
  autopilotCard: {
    backgroundColor: 'rgba(26, 26, 26, 0.9)',
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#10b981',
  },
  autopilotStatus: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#10b981',
    marginBottom: 8,
  },
  autopilotLimit: {
    fontSize: 13,
    color: '#888',
    marginBottom: 16,
  },
  analyzeButton: {
    flexDirection: 'row',
    backgroundColor: '#f97316',
    padding: 14,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  analyzeButtonText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#fff',
  },
  searchContainer: {
    marginTop: 12,
  },
  searchInput: {
    backgroundColor: 'rgba(26, 26, 26, 0.9)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    padding: 16,
    fontSize: 15,
    color: '#fff',
    minHeight: 80,
    marginBottom: 12,
  },
  researchButton: {
    flexDirection: 'row',
    backgroundColor: '#10b981',
    padding: 14,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  researchButtonText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#fff',
  },
  resultsCard: {
    backgroundColor: 'rgba(26, 26, 26, 0.95)',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  consensusBar: {
    marginBottom: 20,
  },
  consensusLabel: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  consensusText: {
    fontSize: 14,
    color: '#888',
  },
  consensusValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#10b981',
  },
  consensusProgress: {
    height: 8,
    backgroundColor: '#2a2a2a',
    borderRadius: 4,
    overflow: 'hidden',
  },
  consensusFill: {
    height: '100%',
    borderRadius: 4,
  },
  aiOpinions: {
    gap: 16,
  },
  aiOpinion: {
    backgroundColor: 'rgba(42, 42, 42, 0.5)',
    padding: 16,
    borderRadius: 12,
  },
  aiName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#f97316',
    marginBottom: 8,
  },
  aiScrollView: {
    maxHeight: 120,
  },
  aiResponse: {
    fontSize: 13,
    color: '#ccc',
    lineHeight: 18,
  },
  disclaimer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 8,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#ef4444',
    flex: 1,
  },
});

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTradingStore } from '../../store/tradingStore';
import { LineChart } from 'react-native-gifted-charts';

const { width } = Dimensions.get('window');

export default function Dashboard() {
  const { account, positions, fetchAccount, fetchPositions, loading } = useTradingStore();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await Promise.all([fetchAccount(), fetchPositions()]);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const totalUnrealizedPL = positions.reduce((sum, pos) => sum + pos.unrealized_pl, 0);
  const portfolioReturn = account ? ((account.portfolio_value - account.cash) / account.cash) * 100 : 0;

  // Mock chart data
  const chartData = [
    { value: 30000 },
    { value: 30500 },
    { value: 31200 },
    { value: 30800 },
    { value: 31500 },
    { value: 32000 },
    { value: account?.portfolio_value || 32395 },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#f97316"
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Willkommen auf dem Court</Text>
            <Text style={styles.userName}>Wookie Mann & Funky Danki</Text>
          </View>
          <MaterialCommunityIcons name="basketball" size={40} color="#f97316" />
        </View>

        {/* Portfolio Value Card */}
        <View style={styles.mainCard}>
          <Text style={styles.cardLabel}>Portfolio-Wert</Text>
          <Text style={styles.mainValue}>
            ${account?.portfolio_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '32,395.40'}
          </Text>
          <View style={styles.returnBadge}>
            <MaterialCommunityIcons
              name={totalUnrealizedPL >= 0 ? 'trending-up' : 'trending-down'}
              size={18}
              color={totalUnrealizedPL >= 0 ? '#10b981' : '#ef4444'}
            />
            <Text
              style={[
                styles.returnText,
                { color: totalUnrealizedPL >= 0 ? '#10b981' : '#ef4444' },
              ]}
            >
              ${Math.abs(totalUnrealizedPL).toFixed(2)} ({portfolioReturn.toFixed(2)}%)
            </Text>
          </View>
        </View>

        {/* Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.sectionTitle}>Performance (7 Tage)</Text>
          <LineChart
            data={chartData}
            width={width - 60}
            height={150}
            color="#f97316"
            thickness={3}
            startFillColor="#f97316"
            endFillColor="#1a1a1a"
            startOpacity={0.4}
            endOpacity={0.1}
            initialSpacing={10}
            spacing={45}
            hideDataPoints
            hideRules
            hideYAxisText
            yAxisColor="transparent"
            xAxisColor="#2a2a2a"
            curved
          />
        </View>

        {/* Quick Stats */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Cash</Text>
            <Text style={styles.statValue}>
              ${account?.cash.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '25,421'}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Buying Power</Text>
            <Text style={styles.statValue}>
              ${account?.buying_power.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '50,842'}
            </Text>
          </View>
        </View>

        {/* Your Lineup (Top Holdings) */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Lineup</Text>
            <MaterialCommunityIcons name="account-group" size={24} color="#f97316" />
          </View>

          {positions.slice(0, 3).map((position, index) => (
            <View key={index} style={styles.positionCard}>
              <View style={styles.positionLeft}>
                <View style={styles.symbolBadge}>
                  <Text style={styles.symbolText}>{position.symbol}</Text>
                </View>
                <View>
                  <Text style={styles.positionQty}>{position.quantity} shares</Text>
                  <Text style={styles.positionPrice}>
                    ${position.current_price.toFixed(2)}
                  </Text>
                </View>
              </View>
              <View style={styles.positionRight}>
                <Text style={styles.positionValue}>
                  ${position.market_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </Text>
                <Text
                  style={[
                    styles.positionPL,
                    { color: position.unrealized_pl >= 0 ? '#10b981' : '#ef4444' },
                  ]}
                >
                  {position.unrealized_pl >= 0 ? '+' : ''}
                  ${position.unrealized_pl.toFixed(2)} ({position.unrealized_plpc.toFixed(2)}%)
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Motivational Quote */}
        <View style={styles.quoteCard}>
          <MaterialCommunityIcons name="format-quote-open" size={24} color="#10b981" />
          <Text style={styles.quoteText}>
            "We can't stop here, this is bat country!" - Keep pushing those gains.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 10,
  },
  greeting: {
    fontSize: 14,
    color: '#888',
    marginBottom: 4,
  },
  userName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  mainCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    marginTop: 10,
    padding: 24,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  cardLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
  },
  mainValue: {
    fontSize: 38,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 12,
  },
  returnBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  returnText: {
    fontSize: 16,
    fontWeight: '600',
  },
  chartCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  statsGrid: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 15,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 6,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  positionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  symbolBadge: {
    backgroundColor: '#f97316',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  symbolText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionQty: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 2,
  },
  positionPrice: {
    fontSize: 12,
    color: '#888',
  },
  positionRight: {
    alignItems: 'flex-end',
  },
  positionValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  positionPL: {
    fontSize: 12,
    fontWeight: '600',
  },
  quoteCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 30,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    flexDirection: 'row',
    gap: 12,
  },
  quoteText: {
    flex: 1,
    fontSize: 14,
    color: '#10b981',
    fontStyle: 'italic',
    lineHeight: 20,
  },
});

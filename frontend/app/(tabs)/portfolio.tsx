import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTradingStore } from '../../store/tradingStore';

export default function Portfolio() {
  const { positions, fetchPositions, loading } = useTradingStore();
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState<'value' | 'return'>('value');

  useEffect(() => {
    fetchPositions();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPositions();
    setRefreshing(false);
  };

  const sortedPositions = [...positions].sort((a, b) => {
    if (sortBy === 'value') {
      return b.market_value - a.market_value;
    } else {
      return b.unrealized_plpc - a.unrealized_plpc;
    }
  });

  const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
  const totalPL = positions.reduce((sum, pos) => sum + pos.unrealized_pl, 0);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Your Lineup</Text>
          <Text style={styles.headerSubtitle}>{positions.length} positions</Text>
        </View>
        <MaterialCommunityIcons name="trophy" size={32} color="#f97316" />
      </View>

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
        {/* Portfolio Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Gesamtwert</Text>
            <Text style={styles.summaryValue}>
              ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Gesamtgewinn</Text>
            <Text
              style={[
                styles.summaryValue,
                { color: totalPL >= 0 ? '#10b981' : '#ef4444' },
              ]}
            >
              {totalPL >= 0 ? '+' : ''}
              ${totalPL.toFixed(2)}
            </Text>
          </View>
        </View>

        {/* Sort Buttons */}
        <View style={styles.sortContainer}>
          <TouchableOpacity
            style={[
              styles.sortButton,
              sortBy === 'value' && styles.sortButtonActive,
            ]}
            onPress={() => setSortBy('value')}
          >
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'value' && styles.sortButtonTextActive,
              ]}
            >
              Nach Wert
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.sortButton,
              sortBy === 'return' && styles.sortButtonActive,
            ]}
            onPress={() => setSortBy('return')}
          >
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'return' && styles.sortButtonTextActive,
              ]}
            >
              Nach Rendite
            </Text>
          </TouchableOpacity>
        </View>

        {/* Positions List */}
        <View style={styles.positionsList}>
          {sortedPositions.map((position, index) => (
            <View key={index} style={styles.positionCard}>
              <View style={styles.positionHeader}>
                <View style={styles.symbolContainer}>
                  <View style={styles.symbolBadge}>
                    <Text style={styles.symbolText}>{position.symbol}</Text>
                  </View>
                  <View>
                    <Text style={styles.positionQty}>
                      {position.quantity} Aktien
                    </Text>
                    <Text style={styles.avgPrice}>
                      Avg: ${position.avg_price.toFixed(2)}
                    </Text>
                  </View>
                </View>
                <View style={styles.valueContainer}>
                  <Text style={styles.currentPrice}>
                    ${position.current_price.toFixed(2)}
                  </Text>
                  <Text style={styles.marketValue}>
                    ${position.market_value.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                    })}
                  </Text>
                </View>
              </View>

              <View style={styles.performanceBar}>
                <View
                  style={[
                    styles.performanceFill,
                    {
                      width: `${Math.min(Math.abs(position.unrealized_plpc) * 5, 100)}%`,
                      backgroundColor:
                        position.unrealized_pl >= 0 ? '#10b981' : '#ef4444',
                    },
                  ]}
                />
              </View>

              <View style={styles.positionFooter}>
                <View>
                  <Text style={styles.plLabel}>Unrealisierter Gewinn/Verlust</Text>
                  <Text
                    style={[
                      styles.plValue,
                      { color: position.unrealized_pl >= 0 ? '#10b981' : '#ef4444' },
                    ]}
                  >
                    {position.unrealized_pl >= 0 ? '+' : ''}
                    ${position.unrealized_pl.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.percentageBadge}>
                  <MaterialCommunityIcons
                    name={position.unrealized_pl >= 0 ? 'trending-up' : 'trending-down'}
                    size={16}
                    color={position.unrealized_pl >= 0 ? '#10b981' : '#ef4444'}
                  />
                  <Text
                    style={[
                      styles.percentageText,
                      { color: position.unrealized_pl >= 0 ? '#10b981' : '#ef4444' },
                    ]}
                  >
                    {position.unrealized_plpc.toFixed(2)}%
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>

        {positions.length === 0 && !loading && (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="basketball" size={64} color="#444" />
            <Text style={styles.emptyText}>No positions yet</Text>
            <Text style={styles.emptySubtext}>Zeit, dein Portfolio aufzubauen!</Text>
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
    color: '#888',
  },
  scrollView: {
    flex: 1,
  },
  summaryCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#888',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  sortContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  sortButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#2a2a2a',
    alignItems: 'center',
  },
  sortButtonActive: {
    backgroundColor: '#f97316',
    borderColor: '#f97316',
  },
  sortButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
  },
  sortButtonTextActive: {
    color: '#fff',
  },
  positionsList: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  positionCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  symbolContainer: {
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
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionQty: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 2,
  },
  avgPrice: {
    fontSize: 12,
    color: '#888',
  },
  valueContainer: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 2,
  },
  marketValue: {
    fontSize: 12,
    color: '#888',
  },
  performanceBar: {
    height: 4,
    backgroundColor: '#2a2a2a',
    borderRadius: 2,
    marginBottom: 12,
    overflow: 'hidden',
  },
  performanceFill: {
    height: '100%',
    borderRadius: 2,
  },
  positionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  plLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  plValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  percentageBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#0a0a0a',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  percentageText: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#444',
    marginTop: 8,
  },
});

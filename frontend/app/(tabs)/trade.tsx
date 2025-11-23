import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTradingStore } from '../../store/tradingStore';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export default function Trade() {
  const { account, fetchQuote, placeOrder, fetchAccount, fetchPositions } = useTradingStore();
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [limitPrice, setLimitPrice] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [currentQuote, setCurrentQuote] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (symbol.length >= 1) {
      searchStocks(symbol);
    } else {
      setSearchResults([]);
      setCurrentQuote(null);
    }
  }, [symbol]);

  const searchStocks = async (query: string) => {
    try {
      setIsSearching(true);
      const response = await axios.get(`${API_URL}/api/search/${query}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const selectStock = async (stock: any) => {
    setSymbol(stock.symbol);
    setSearchResults([]);
    
    // Fetch current quote
    const quote = await fetchQuote(stock.symbol);
    setCurrentQuote(quote);
  };

  const handlePlaceOrder = async () => {
    if (!symbol || !quantity) {
      Alert.alert('Error', 'Please enter symbol and quantity');
      return;
    }

    if (orderType === 'limit' && !limitPrice) {
      Alert.alert('Error', 'Please enter limit price');
      return;
    }

    try {
      const orderData = {
        symbol: symbol.toUpperCase(),
        quantity: parseFloat(quantity),
        side,
        order_type: orderType,
        limit_price: orderType === 'limit' ? parseFloat(limitPrice) : null,
      };

      await placeOrder(orderData);
      Alert.alert(
        'Order Placed!',
        `${side.toUpperCase()} ${quantity} shares of ${symbol.toUpperCase()}`,
        [
          {
            text: 'OK',
            onPress: () => {
              setSymbol('');
              setQuantity('');
              setLimitPrice('');
              setCurrentQuote(null);
              fetchAccount();
              fetchPositions();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Order Failed', 'Unable to place order. Please try again.');
    }
  };

  const estimatedCost = currentQuote && quantity
    ? (parseFloat(quantity) * currentQuote.price).toFixed(2)
    : '0.00';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Trade ausführen</Text>
            <Text style={styles.headerSubtitle}>Führe deine Trades aus</Text>
          </View>
          <MaterialCommunityIcons name="rocket-launch" size={32} color="#10b981" />
        </View>

        <ScrollView style={styles.scrollView} keyboardShouldPersistTaps="handled">
          {/* Balance Card */}
          <View style={styles.balanceCard}>
            <View style={styles.balanceRow}>
              <Text style={styles.balanceLabel}>Verfügbares Bargeld</Text>
              <Text style={styles.balanceValue}>
                ${account?.cash.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
              </Text>
            </View>
            <View style={styles.balanceRow}>
              <Text style={styles.balanceLabel}>Kaufkraft</Text>
              <Text style={styles.balanceValue}>
                ${account?.buying_power.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
              </Text>
            </View>
          </View>

          {/* Stock Search */}
          <View style={styles.inputSection}>
            <Text style={styles.inputLabel}>Aktiensymbol</Text>
            <View style={styles.searchContainer}>
              <MaterialCommunityIcons
                name="magnify"
                size={20}
                color="#888"
                style={styles.searchIcon}
              />
              <TextInput
                style={styles.searchInput}
                placeholder="Aktien suchen (e.g., AAPL)"
                placeholderTextColor="#666"
                value={symbol}
                onChangeText={setSymbol}
                autoCapitalize="characters"
              />
            </View>

            {searchResults.length > 0 && (
              <View style={styles.searchResults}>
                {searchResults.map((stock, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.searchResultItem}
                    onPress={() => selectStock(stock)}
                  >
                    <View>
                      <Text style={styles.resultSymbol}>{stock.symbol}</Text>
                      <Text style={styles.resultName}>{stock.name}</Text>
                    </View>
                    <Text style={styles.resultPrice}>${stock.price}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          {/* Current Quote */}
          {currentQuote && (
            <>
              <View style={styles.quoteCard}>
                <Text style={styles.quoteSymbol}>{currentQuote.symbol}</Text>
                <Text style={styles.quotePrice}>${currentQuote.price.toFixed(2)}</Text>
                <View style={styles.quoteBidAsk}>
                  <Text style={styles.quoteBidAskText}>Bid: ${currentQuote.bid.toFixed(2)}</Text>
                  <Text style={styles.quoteBidAskText}>Ask: ${currentQuote.ask.toFixed(2)}</Text>
                </View>
              </View>

              {/* Firmeninformationen */}
              <View style={styles.companyInfoCard}>
                <View style={styles.infoHeader}>
                  <MaterialCommunityIcons name="information" size={20} color="#f97316" />
                  <Text style={styles.infoHeaderText}>Firmeninformationen</Text>
                </View>
                
                {currentQuote.symbol === 'AAPL' && (
                  <>
                    <Text style={styles.companyName}>Apple Inc.</Text>
                    <Text style={styles.companyDesc}>
                      Apple entwickelt, produziert und verkauft Smartphones, Computer, Tablets und Wearables. 
                      Marktführer im Premium-Segment.
                    </Text>
                    <View style={styles.infoGrid}>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Marktkapitalisierung</Text>
                        <Text style={styles.infoValue}>$2.8T</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Hoch</Text>
                        <Text style={styles.infoValue}>$199.62</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Tief</Text>
                        <Text style={styles.infoValue}>$164.08</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Durchschn. Volumen</Text>
                        <Text style={styles.infoValue}>52.4M</Text>
                      </View>
                    </View>
                  </>
                )}
                
                {currentQuote.symbol === 'TSLA' && (
                  <>
                    <Text style={styles.companyName}>Tesla Inc.</Text>
                    <Text style={styles.companyDesc}>
                      Tesla entwickelt und produziert Elektrofahrzeuge, Batteriespeicher und Solarpanels. 
                      Pionier der Elektromobilität.
                    </Text>
                    <View style={styles.infoGrid}>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Marktkapitalisierung</Text>
                        <Text style={styles.infoValue}>$800B</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Hoch</Text>
                        <Text style={styles.infoValue}>$299.29</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Tief</Text>
                        <Text style={styles.infoValue}>$138.80</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Durchschn. Volumen</Text>
                        <Text style={styles.infoValue}>98.7M</Text>
                      </View>
                    </View>
                  </>
                )}
                
                {currentQuote.symbol === 'NVDA' && (
                  <>
                    <Text style={styles.companyName}>NVIDIA Corporation</Text>
                    <Text style={styles.companyDesc}>
                      NVIDIA entwickelt Grafikprozessoren und KI-Chips. Marktführer bei GPUs für Gaming, 
                      Rechenzentren und künstliche Intelligenz.
                    </Text>
                    <View style={styles.infoGrid}>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Marktkapitalisierung</Text>
                        <Text style={styles.infoValue}>$1.2T</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Hoch</Text>
                        <Text style={styles.infoValue}>$505.48</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>52-Wochen-Tief</Text>
                        <Text style={styles.infoValue}>$108.13</Text>
                      </View>
                      <View style={styles.infoItem}>
                        <Text style={styles.infoLabel}>Durchschn. Volumen</Text>
                        <Text style={styles.infoValue}>320M</Text>
                      </View>
                    </View>
                  </>
                )}
                
                {!['AAPL', 'TSLA', 'NVDA'].includes(currentQuote.symbol) && (
                  <>
                    <Text style={styles.companyName}>{currentQuote.symbol}</Text>
                    <Text style={styles.companyDesc}>
                      Öffentlich gehandeltes Unternehmen. Weitere Informationen sind verfügbar nach der Marktanalyse.
                    </Text>
                  </>
                )}
              </View>
            </>
          )}

          {/* Order-Typ Toggle */}
          <View style={styles.inputSection}>
            <Text style={styles.inputLabel}>Order-Typ</Text>
            <View style={styles.toggleContainer}>
              <TouchableOpacity
                style={[
                  styles.toggleButton,
                  orderType === 'market' && styles.toggleButtonActive,
                ]}
                onPress={() => setOrderType('market')}
              >
                <Text
                  style={[
                    styles.toggleButtonText,
                    orderType === 'market' && styles.toggleButtonTextActive,
                  ]}
                >
                  Market
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.toggleButton,
                  orderType === 'limit' && styles.toggleButtonActive,
                ]}
                onPress={() => setOrderType('limit')}
              >
                <Text
                  style={[
                    styles.toggleButtonText,
                    orderType === 'limit' && styles.toggleButtonTextActive,
                  ]}
                >
                  Limit
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Quantity Input */}
          <View style={styles.inputSection}>
            <Text style={styles.inputLabel}>Anzahl (Aktien)</Text>
            <TextInput
              style={styles.input}
              placeholder="0"
              placeholderTextColor="#666"
              value={quantity}
              onChangeText={setQuantity}
              keyboardType="decimal-pad"
            />
          </View>

          {/* Limit-Preis (only for limit orders) */}
          {orderType === 'limit' && (
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Limit-Preis</Text>
              <TextInput
                style={styles.input}
                placeholder="0.00"
                placeholderTextColor="#666"
                value={limitPrice}
                onChangeText={setLimitPrice}
                keyboardType="decimal-pad"
              />
            </View>
          )}

          {/* Geschätzte Kosten */}
          {quantity && currentQuote && (
            <View style={styles.estimateCard}>
              <Text style={styles.estimateLabel}>Geschätzte Kosten</Text>
              <Text style={styles.estimateValue}>${estimatedCost}</Text>
            </View>
          )}

          {/* Buy/Sell Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.actionButton, styles.buyButton]}
              onPress={() => {
                setSide('buy');
                handlePlaceOrder();
              }}
              disabled={!symbol || !quantity}
            >
              <MaterialCommunityIcons name="trending-up" size={24} color="#fff" />
              <Text style={styles.actionButtonText}>KAUFEN</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.sellButton]}
              onPress={() => {
                setSide('sell');
                handlePlaceOrder();
              }}
              disabled={!symbol || !quantity}
            >
              <MaterialCommunityIcons name="trending-down" size={24} color="#fff" />
              <Text style={styles.actionButtonText}>VERKAUFEN</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.disclaimer}>
            <MaterialCommunityIcons name="information" size={16} color="#666" />
            <Text style={styles.disclaimerText}>
              Paper-Trading-Umgebung - kein echtes Geld
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  keyboardView: {
    flex: 1,
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
  balanceCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  balanceLabel: {
    fontSize: 14,
    color: '#888',
  },
  balanceValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  inputSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ccc',
    marginBottom: 8,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    paddingHorizontal: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
    paddingVertical: 14,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  searchResults: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    maxHeight: 200,
  },
  searchResultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  resultSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 2,
  },
  resultName: {
    fontSize: 12,
    color: '#888',
  },
  resultPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10b981',
  },
  quoteCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#f97316',
    alignItems: 'center',
  },
  quoteSymbol: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#f97316',
    marginBottom: 8,
  },
  quotePrice: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  quoteBidAsk: {
    flexDirection: 'row',
    gap: 20,
  },
  quoteBidAskText: {
    fontSize: 12,
    color: '#888',
  },
  toggleContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#2a2a2a',
    alignItems: 'center',
  },
  toggleButtonActive: {
    backgroundColor: '#f97316',
    borderColor: '#f97316',
  },
  toggleButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
  },
  toggleButtonTextActive: {
    color: '#fff',
  },
  estimateCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  estimateLabel: {
    fontSize: 14,
    color: '#888',
  },
  estimateValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 12,
    marginBottom: 20,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 18,
    borderRadius: 12,
    gap: 8,
  },
  buyButton: {
    backgroundColor: '#10b981',
  },
  sellButton: {
    backgroundColor: '#ef4444',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
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
    fontSize: 12,
    color: '#666',
  },
});

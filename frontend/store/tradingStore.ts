import { create } from 'zustand';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
}

interface Account {
  cash: number;
  portfolio_value: number;
  buying_power: number;
  equity: number;
}

interface Quote {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  timestamp: string;
}

interface TradingState {
  account: Account | null;
  positions: Position[];
  quotes: Record<string, Quote>;
  loading: boolean;
  error: string | null;
  fetchAccount: () => Promise<void>;
  fetchPositions: () => Promise<void>;
  fetchQuote: (symbol: string) => Promise<Quote | null>;
  placeOrder: (orderData: any) => Promise<any>;
}

export const useTradingStore = create<TradingState>((set, get) => ({
  account: null,
  positions: [],
  quotes: {},
  loading: false,
  error: null,

  fetchAccount: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get(`${API_URL}/api/account`);
      set({ account: response.data, loading: false });
    } catch (error: any) {
      console.error('Error fetching account:', error);
      set({ error: error.message, loading: false });
    }
  },

  fetchPositions: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get(`${API_URL}/api/positions`);
      set({ positions: response.data, loading: false });
    } catch (error: any) {
      console.error('Error fetching positions:', error);
      set({ error: error.message, loading: false });
    }
  },

  fetchQuote: async (symbol: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/quote/${symbol}`);
      const quote = response.data;
      set((state) => ({
        quotes: { ...state.quotes, [symbol]: quote },
      }));
      return quote;
    } catch (error: any) {
      console.error('Error fetching quote:', error);
      set({ error: error.message });
      return null;
    }
  },

  placeOrder: async (orderData: any) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/api/orders`, orderData);
      set({ loading: false });
      return response.data;
    } catch (error: any) {
      console.error('Error placing order:', error);
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#1a1a1a',
          borderTopColor: '#2a2a2a',
          borderTopWidth: 1,
          height: 65,
          paddingBottom: 10,
          paddingTop: 8,
        },
        tabBarActiveTintColor: '#f97316',
        tabBarInactiveTintColor: '#666',
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Übersicht',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="view-dashboard" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="portfolio"
        options={{
          title: 'Portfolio',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="briefcase" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="trade"
        options={{
          title: 'Handeln',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="basket" size={size + 4} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="agenten"
        options={{
          title: 'Agenten',
          tabBarIcon: ({ color, size}) => (
            <MaterialCommunityIcons name="robot" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="ai-zentrale"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="ai-dashboard"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Coach',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="robot" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, DollarSign, Users, Award } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

export default function AnalyticsDashboard({ projectId }) {
  const [productivity, setProductivity] = useState(null);
  const [costSavings, setCostSavings] = useState(null);
  const [techHeatmap, setTechHeatmap] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, [projectId]);

  const fetchAnalytics = async () => {
    try {
      const [prodRes, costRes, heatmapRes] = await Promise.all([
        api.get(`/analytics/${projectId}/productivity?days=30`),
        api.get(`/analytics/${projectId}/cost-savings?days=30`),
        api.get(`/analytics/${projectId}/technology-heatmap`)
      ]);
      
      setProductivity(prodRes.data);
      setCostSavings(costRes.data);
      setTechHeatmap(heatmapRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Analytics Dashboard</h1>

      {/* Metrics Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg text-white shadow-lg"
        >
          <div className="flex items-center justify-between mb-2">
            <TrendingUp size={32} />
            <span className="text-3xl font-bold">{productivity?.files_improved || 0}</span>
          </div>
          <p className="text-sm opacity-90">Files Improved</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 bg-gradient-to-br from-green-500 to-green-600 rounded-lg text-white shadow-lg"
        >
          <div className="flex items-center justify-between mb-2">
            <DollarSign size={32} />
            <span className="text-3xl font-bold">
              ${(costSavings?.total_cost_savings || 0).toLocaleString()}
            </span>
          </div>
          <p className="text-sm opacity-90">Cost Savings</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg text-white shadow-lg"
        >
          <div className="flex items-center justify-between mb-2">
            <Users size={32} />
            <span className="text-3xl font-bold">{costSavings?.developer_hours_saved || 0}</span>
          </div>
          <p className="text-sm opacity-90">Hours Saved</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-6 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg text-white shadow-lg"
        >
          <div className="flex items-center justify-between mb-2">
            <Award size={32} />
            <span className="text-3xl font-bold">
              {productivity?.improvement_rate?.toFixed(1) || 0}%
            </span>
          </div>
          <p className="text-sm opacity-90">Improvement Rate</p>
        </motion.div>
      </div>

      {/* Cost Savings Breakdown */}
      {costSavings && (
        <div className="mb-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Cost Savings Breakdown</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">Critical Bugs Prevented</p>
              <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                {costSavings.breakdown.critical_bugs_prevented}
              </p>
              <p className="text-sm text-gray-500 mt-2">$5,000 each</p>
            </div>

            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">High Priority Bugs</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                {costSavings.breakdown.high_bugs_prevented}
              </p>
              <p className="text-sm text-gray-500 mt-2">$2,000 each</p>
            </div>

            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">Medium Priority Bugs</p>
              <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                {costSavings.breakdown.medium_bugs_prevented}
              </p>
              <p className="text-sm text-gray-500 mt-2">$500 each</p>
            </div>
          </div>
        </div>
      )}

      {/* Technology Heatmap */}
      {techHeatmap && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Technology Risk Heatmap</h2>
          <div className="space-y-3">
            {Object.entries(techHeatmap.technologies).slice(0, 10).map(([tech, stats], index) => (
              <div key={tech} className="flex items-center gap-4">
                <div className="w-32 text-sm font-medium capitalize">{tech}</div>
                <div className="flex-1">
                  <div className="relative h-8 bg-gray-200 dark:bg-gray-700 rounded">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${stats.average_risk * 100}%` }}
                      transition={{ delay: index * 0.1 }}
                      className="absolute h-full rounded bg-gradient-to-r from-yellow-500 to-red-500"
                    />
                  </div>
                </div>
                <div className="w-20 text-right text-sm font-semibold">
                  {(stats.average_risk * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Save, X } from 'lucide-react';
import api from '../services/api';

export default function AdvancedSearch({ projectId }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [filters, setFilters] = useState({
    severity: [],
    minRisk: 0,
    fileTypes: []
  });
  const [savedFilters, setSavedFilters] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadSavedFilters();
  }, []);

  const loadSavedFilters = async () => {
    try {
      const response = await api.get('/search/filters/user_123');
      setSavedFilters(response.data.filters);
    } catch (error) {
      console.error('Failed to load filters:', error);
    }
  };

  const search = async () => {
    try {
      const response = await api.post(`/search/${projectId}`, {
        query,
        filters: {
          severity: filters.severity.length > 0 ? filters.severity : null,
          min_risk_score: filters.minRisk > 0 ? filters.minRisk / 100 : null,
          file_types: filters.fileTypes.length > 0 ? filters.fileTypes : null
        }
      });
      setResults(response.data.results);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const saveCurrentFilter = async () => {
    const filterName = prompt('Enter filter name:');
    if (!filterName) return;

    try {
      await api.post('/search/filters/save', {
        user_id: 'user_123',
        filter_name: filterName,
        conditions: filters
      });
      loadSavedFilters();
    } catch (error) {
      console.error('Failed to save filter:', error);
    }
  };

  const applyFilter = (filter) => {
    setFilters(filter.conditions);
  };

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6">Advanced Search</h2>

      {/* Search Bar */}
      <div className="flex gap-2 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 text-gray-400" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && search()}
            placeholder="Search files, code patterns, issues..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-2"
        >
          <Filter size={20} />
          Filters
        </button>
        <button
          onClick={search}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Search
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-4 p-4 bg-gray-50 dark:bg-gray-750 rounded-lg"
        >
          <div className="grid grid-cols-3 gap-4">
            {/* Severity Filter */}
            <div>
              <label className="block text-sm font-medium mb-2">Severity</label>
              <div className="space-y-2">
                {['critical', 'high', 'medium', 'low'].map((severity) => (
                  <label key={severity} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.severity.includes(severity)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters({...filters, severity: [...filters.severity, severity]});
                        } else {
                          setFilters({...filters, severity: filters.severity.filter(s => s !== severity)});
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="capitalize">{severity}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Risk Score Filter */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Min Risk Score: {filters.minRisk}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.minRisk}
                onChange={(e) => setFilters({...filters, minRisk: parseInt(e.target.value)})}
                className="w-full"
              />
            </div>

            {/* File Types */}
            <div>
              <label className="block text-sm font-medium mb-2">File Types</label>
              <div className="space-y-2">
                {['python', 'javascript', 'java', 'cpp'].map((type) => (
                  <label key={type} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.fileTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters({...filters, fileTypes: [...filters.fileTypes, type]});
                        } else {
                          setFilters({...filters, fileTypes: filters.fileTypes.filter(t => t !== type)});
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="capitalize">{type}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={saveCurrentFilter}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2"
            >
              <Save size={16} />
              Save Filter
            </button>
            <button
              onClick={() => setFilters({ severity: [], minRisk: 0, fileTypes: [] })}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-600 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500"
            >
              Clear Filters
            </button>
          </div>
        </motion.div>
      )}

      {/* Saved Filters */}
      {savedFilters.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium mb-2">Saved Filters:</h3>
          <div className="flex flex-wrap gap-2">
            {savedFilters.map((filter) => (
              <button
                key={filter.name}
                onClick={() => applyFilter(filter)}
                className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm hover:bg-blue-200 dark:hover:bg-blue-800"
              >
                {filter.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">
          {results.length} Results
        </h3>
        {results.map((result, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-4 bg-gray-50 dark:bg-gray-750 rounded-lg"
          >
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium">{result.path}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Risk Score: {(result.risk_score * 100).toFixed(1)}%
                </p>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                result.risk_score >= 0.8 ? 'bg-red-100 text-red-700' :
                result.risk_score >= 0.6 ? 'bg-orange-100 text-orange-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {result.risk_score >= 0.8 ? 'Critical' :
                 result.risk_score >= 0.6 ? 'High' : 'Medium'}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

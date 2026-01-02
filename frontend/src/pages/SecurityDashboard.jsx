import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Key, Lock, Database } from 'lucide-react';
import api from '../services/api';

export default function SecurityDashboard({ projectId }) {
  const [securityScore, setSecurityScore] = useState(null);
  const [secrets, setSecrets] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);

  useEffect(() => {
    fetchSecurityData();
  }, [projectId]);

  const fetchSecurityData = async () => {
    try {
      const [scoreRes, secretsRes, vulnRes] = await Promise.all([
        api.get(`/security/${projectId}/score`),
        api.get(`/security/${projectId}/secrets`),
        api.get(`/security/${projectId}/vulnerabilities`)
      ]);
      
      setSecurityScore(scoreRes.data);
      setSecrets(secretsRes.data.secrets);
      setVulnerabilities(vulnRes.data.vulnerabilities);
    } catch (error) {
      console.error('Failed to fetch security data:', error);
    }
  };

  const getGradeColor = (grade) => {
    const colors = {
      'A': 'text-green-500',
      'B': 'text-blue-500',
      'C': 'text-yellow-500',
      'D': 'text-orange-500',
      'F': 'text-red-500'
    };
    return colors[grade] || 'text-gray-500';
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Security Dashboard</h1>

      {/* Security Score Card */}
      {securityScore && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">Security Score</h2>
              <p className="text-blue-100">{securityScore.recommendation}</p>
            </div>
            <div className="text-center">
              <div className={`text-6xl font-bold ${getGradeColor(securityScore.grade)}`}>
                {securityScore.grade}
              </div>
              <div className="text-3xl font-semibold mt-2">
                {securityScore.security_score}/100
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="flex items-center gap-3">
            <Key className="text-red-500" size={32} />
            <div>
              <p className="text-2xl font-bold">{secrets.length}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Exposed Secrets</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-orange-500" size={32} />
            <div>
              <p className="text-2xl font-bold">{vulnerabilities.length}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Vulnerabilities</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="flex items-center gap-3">
            <Shield className="text-green-500" size={32} />
            <div>
              <p className="text-2xl font-bold">{securityScore?.security_score || 0}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Security Score</p>
            </div>
          </div>
        </div>
      </div>

      {/* Secrets List */}
      {secrets.length > 0 && (
        <div className="mb-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Key className="text-red-500" />
            Exposed Secrets
          </h3>
          <div className="space-y-2">
            {secrets.map((secret, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-red-700 dark:text-red-400">
                      {secret.type.replace('_', ' ').toUpperCase()}
                    </h4>
                    <p className="text-sm mt-1">{secret.file}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Line {secret.line}</p>
                  </div>
                  <span className="px-3 py-1 bg-red-500 text-white text-xs rounded-full">
                    CRITICAL
                  </span>
                </div>
                <p className="mt-2 text-sm">{secret.message}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Vulnerabilities List */}
      {vulnerabilities.length > 0 && (
        <div>
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <AlertTriangle className="text-orange-500" />
            OWASP Vulnerabilities
          </h3>
          <div className="space-y-2">
            {vulnerabilities.map((vuln, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`p-4 rounded border-l-4 ${
                  vuln.severity === 'critical' ? 'bg-red-50 dark:bg-red-900/20 border-red-500' :
                  vuln.severity === 'high' ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-500' :
                  'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{vuln.message}</h4>
                    <p className="text-sm mt-1">{vuln.file}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Line {vuln.line} • {vuln.owasp_category}
                    </p>
                  </div>
                  <span className={`px-3 py-1 text-xs rounded-full ${
                    vuln.severity === 'critical' ? 'bg-red-500 text-white' :
                    vuln.severity === 'high' ? 'bg-orange-500 text-white' :
                    'bg-yellow-500 text-white'
                  }`}>
                    {vuln.severity.toUpperCase()}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const express = require('express');
const router = express.Router();
const performanceService = require('../services/performanceService');

// GET /api/health
router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'KATSU Performance Intelligence',
    version: '1.0.0'
  });
});

// GET /api/games
router.get('/games', (req, res) => {
  res.json(performanceService.getGamesCatalog());
});

// GET /api/device
router.get('/device', (req, res) => {
  res.json(performanceService.getDeviceInfo());
});

// POST /api/analyze
router.post('/analyze', (req, res) => {
  try {
    const analysis = performanceService.analyzePerformance(req.body);
    res.json(analysis);
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(400).json({ error: error.message || 'Failed to analyze performance' });
  }
});

module.exports = router;

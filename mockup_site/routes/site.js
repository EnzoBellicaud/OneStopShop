const express = require('express');
const db = require('../db');
const { OPPORTUNITY_TYPES } = require('../constants');

const router = express.Router();

router.get('/', (req, res) => {
  const recent = db
    .prepare('SELECT * FROM opportunities ORDER BY created_at DESC, id DESC LIMIT 6')
    .all();

  res.render('home', { recent });
});

router.get('/opportunities', (req, res) => {
  const { type } = req.query;

  let opportunities;
  if (type) {
    opportunities = db
      .prepare('SELECT * FROM opportunities WHERE type = ? ORDER BY created_at DESC, id DESC')
      .all(type);
  } else {
    opportunities = db
      .prepare('SELECT * FROM opportunities ORDER BY created_at DESC, id DESC')
      .all();
  }

  res.render('opportunities', {
    opportunities,
    types: OPPORTUNITY_TYPES,
    selectedType: type || ''
  });
});

router.get('/opportunities/:id', (req, res) => {
  const opportunity = db
    .prepare('SELECT * FROM opportunities WHERE id = ?')
    .get(req.params.id);

  if (!opportunity) {
    return res.status(404).render('not-found');
  }

  res.render('opportunity', { opportunity });
});

router.get('/about', (req, res) => {
  res.render('about');
});

module.exports = router;

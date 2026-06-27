const express = require('express');
const db = require('../db');
const { OPPORTUNITY_TYPES } = require('../constants');

const router = express.Router();

const FIELDS = ['title', 'type', 'department', 'description', 'location', 'deadline', 'link_url'];

// Convert empty strings from form submission to null so the DB stores true NULLs
function normalize(body) {
  const data = {};
  for (const field of FIELDS) {
    const value = body[field];
    data[field] = value === undefined || value === '' ? null : value;
  }
  return data;
}

router.get('/', (req, res) => {
  const opportunities = db
    .prepare('SELECT * FROM opportunities ORDER BY id DESC')
    .all();

  res.render('admin', {
    opportunities,
    types: OPPORTUNITY_TYPES,
    editing: null
  });
});

router.get('/opportunities/:id/edit', (req, res) => {
  const opportunities = db
    .prepare('SELECT * FROM opportunities ORDER BY id DESC')
    .all();

  const editing = db
    .prepare('SELECT * FROM opportunities WHERE id = ?')
    .get(req.params.id);

  if (!editing) {
    return res.status(404).render('not-found');
  }

  res.render('admin', {
    opportunities,
    types: OPPORTUNITY_TYPES,
    editing
  });
});

router.post('/opportunities', (req, res) => {
  const data = normalize(req.body);
  data.created_at = new Date().toISOString().slice(0, 10);

  db.prepare(`
    INSERT INTO opportunities (title, type, department, description, location, deadline, link_url, created_at)
    VALUES (@title, @type, @department, @description, @location, @deadline, @link_url, @created_at)
  `).run(data);

  res.redirect('/admin');
});

router.put('/opportunities/:id', (req, res) => {
  const data = normalize(req.body);
  data.id = req.params.id;

  db.prepare(`
    UPDATE opportunities
    SET title = @title, type = @type, department = @department, description = @description,
        location = @location, deadline = @deadline, link_url = @link_url
    WHERE id = @id
  `).run(data);

  res.redirect('/admin');
});

router.delete('/opportunities/:id', (req, res) => {
  db.prepare('DELETE FROM opportunities WHERE id = ?').run(req.params.id);
  res.redirect('/admin');
});

module.exports = router;

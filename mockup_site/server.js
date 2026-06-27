const express = require('express');
const path = require('path');
const methodOverride = require('method-override');

const siteRoutes = require('./routes/site');
const adminRoutes = require('./routes/admin');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.urlencoded({ extended: true }));
app.use(methodOverride('_method'));
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', siteRoutes);
app.use('/admin', adminRoutes);

app.listen(PORT, () => {
  console.log(`Université de Valmoure mock site running at http://localhost:${PORT}`);
});

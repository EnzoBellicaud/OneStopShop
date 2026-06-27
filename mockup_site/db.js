const path = require('path');
const Database = require('better-sqlite3');

const db = new Database(path.join(__dirname, 'data.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    type TEXT,
    department TEXT,
    description TEXT,
    location TEXT,
    deadline TEXT,
    link_url TEXT,
    created_at TEXT
  )
`);

const count = db.prepare('SELECT COUNT(*) AS n FROM opportunities').get().n;

if (count === 0) {
  const insert = db.prepare(`
    INSERT INTO opportunities (title, type, department, description, location, deadline, link_url, created_at)
    VALUES (@title, @type, @department, @description, @location, @deadline, @link_url, @created_at)
  `);

  const seed = [
    {
      title: 'MSc in Artificial Intelligence',
      type: 'Program',
      department: 'Computer Science',
      description: 'A two-year master\'s program covering machine learning, computer vision, natural language processing and AI ethics. Includes a mandatory research thesis in the final year.',
      location: 'Campus Nord, Building B',
      deadline: '2026-07-15',
      link_url: 'https://www.valmoure.edu/programs/msc-ai',
      created_at: '2026-05-02'
    },
    {
      title: 'Introduction to Quantum Computing',
      type: 'Course',
      department: 'Physics',
      description: 'An undergraduate elective introducing the principles of quantum computation, qubits, and quantum algorithms. Open to second-year students and above.',
      location: 'Campus Sud, Room 214',
      deadline: null,
      link_url: 'https://www.valmoure.edu/courses/quantum-computing-101',
      created_at: '2026-04-20'
    },
    {
      title: 'Research Position: Sustainable Materials Lab',
      type: 'Research',
      department: 'Materials Engineering',
      description: 'The Sustainable Materials Lab is seeking a research assistant to work on biodegradable polymer composites. Funded position for 12 months, renewable.',
      location: 'Innovation Park, Lab 4',
      deadline: '2026-08-01',
      link_url: 'https://www.valmoure.edu/research/sustainable-materials',
      created_at: '2026-05-28'
    },
    {
      title: 'Summer Internship - Data Engineering Team',
      type: 'Internship',
      department: 'IT Services',
      description: 'Join the university IT Services data engineering team for a 10-week summer internship. Work on real data pipelines supporting student services.',
      location: null,
      deadline: '2026-06-30',
      link_url: 'https://www.valmoure.edu/internships/data-engineering',
      created_at: '2026-05-10'
    },
    {
      title: 'Valmoure AI Hackathon 2026',
      type: 'Event',
      department: 'Student Innovation Office',
      description: '48-hour hackathon open to all students. Teams will build AI-powered tools to address campus sustainability challenges. Prizes for top three teams.',
      location: 'Main Auditorium',
      deadline: '2026-09-12',
      link_url: 'https://www.valmoure.edu/events/ai-hackathon-2026',
      created_at: '2026-06-01'
    },
    {
      title: 'Thesis Subject: Federated Learning for Healthcare',
      type: 'Thesis',
      department: 'Computer Science',
      description: 'Looking for a final-year master\'s student to explore federated learning techniques applied to privacy-preserving healthcare data analysis.',
      location: 'Campus Nord, Building B',
      deadline: null,
      link_url: null,
      created_at: '2026-05-15'
    },
    {
      title: 'Erasmus Exchange Semester - University of Lund',
      type: 'Program',
      department: 'International Relations Office',
      description: null,
      location: null,
      deadline: '2026-07-31',
      link_url: 'https://www.valmoure.edu/exchange/lund',
      created_at: '2026-04-28'
    },
    {
      title: 'Open Day for Prospective Students',
      type: 'Event',
      department: null,
      description: 'Visit our campuses, meet faculty members and current students, and learn more about our undergraduate and graduate programs.',
      location: 'All Campuses',
      deadline: '2026-10-05',
      link_url: null,
      created_at: '2026-06-05'
    },
    {
      title: 'Advanced Topics in Robotics',
      type: 'Course',
      department: 'Mechanical Engineering',
      description: 'A graduate-level course covering kinematics, control systems, and applications of robotics in industry and research.',
      location: 'Campus Nord, Robotics Hall',
      deadline: null,
      link_url: 'https://www.valmoure.edu/courses/advanced-robotics',
      created_at: '2026-05-20'
    },
    {
      title: 'Untitled Listing',
      type: null,
      department: null,
      description: null,
      location: null,
      deadline: null,
      link_url: null,
      created_at: '2026-06-10'
    }
  ];

  const insertMany = db.transaction((rows) => {
    for (const row of rows) insert.run(row);
  });
  insertMany(seed);
}

module.exports = db;

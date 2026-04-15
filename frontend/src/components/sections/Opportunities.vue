<template>
    <section id="opportunities">
        <div class="section-header">
            <div>
            <p class="section-eyebrow">Latest listings</p>
            <h2 class="section-title">Browse opportunities</h2>
            </div>
            <a class="section-link" href="#">View all →</a>
        </div>

        <div class="filter-bar">
            <input class="search-input" type="text" placeholder="Search by keyword, topic, department...">
            <select class="filter-select">
            <option>All universities</option>
            <option>KTH Royal Institute</option>
            <option>Uppsala University</option>
            <option>Lund University</option>
            <option>Chalmers</option>
            <option>Linköping University</option>
            </select>
            <button class="filter-chip active">All</button>
            <button class="filter-chip">Thesis</button>
            <button class="filter-chip">Internship</button>
            <button class="filter-chip">Jobs</button>
            <button class="filter-chip">Courses</button>
        </div>

        <div class="cards-grid">

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-thesis">Master thesis</span>
                <div class="uni-logo-sm">KTH</div>
            </div>
            <div class="card-title">AI-driven energy optimisation in smart grid systems</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                KTH Royal Institute of Technology
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Full-time · 6 months
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Stockholm, Sweden
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Deadline: 15 May 2026</span>
                <a class="btn-view" href="#">View at KTH</a>
            </div>
            </div>

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-intern">Internship</span>
                <div class="uni-logo-sm">LU</div>
            </div>
            <div class="card-title">Sustainability research intern — Materials Science Lab</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                Lund University
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Part-time · 3 months
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Lund, Sweden
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Deadline: 1 Jun 2026</span>
                <a class="btn-view" href="#">View at Lund</a>
            </div>
            </div>

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-job">Job opportunity</span>
                <div class="uni-logo-sm">UU</div>
            </div>
            <div class="card-title">Research assistant — Computational Biology department</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                Uppsala University
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Full-time · Permanent
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Uppsala, Sweden
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Open until filled</span>
                <a class="btn-view" href="#">View at Uppsala</a>
            </div>
            </div>

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-course">Course</span>
                <div class="uni-logo-sm">CTH</div>
            </div>
            <div class="card-title">Advanced Machine Learning — Spring 2026 open enrolment</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                Chalmers University
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                7.5 credits · Semester
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Gothenburg / Online
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Enrol by: 20 May 2026</span>
                <a class="btn-view" href="#">View at Chalmers</a>
            </div>
            </div>

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-thesis">Master thesis</span>
                <div class="uni-logo-sm">LiU</div>
            </div>
            <div class="card-title">Human-computer interaction in mixed-reality environments</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                Linköping University
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Full-time · 6 months
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Linköping, Sweden
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Deadline: 30 Apr 2026</span>
                <a class="btn-view" href="#">View at LiU</a>
            </div>
            </div>

            <div class="opp-card">
            <div class="card-top">
                <span class="type-tag tag-intern">Internship</span>
                <div class="uni-logo-sm">SU</div>
            </div>
            <div class="card-title">Digital marketing & communications intern — Business School</div>
            <div class="card-meta">
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
                Stockholm University
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Part-time · 4 months
                </div>
                <div class="card-meta-row">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                Stockholm, Sweden
                </div>
            </div>
            <div class="card-footer">
                <span class="deadline">Deadline: 10 Jun 2026</span>
                <a class="btn-view" href="#">View at SU</a>
            </div>
            </div>

        </div>
    </section>
</template>
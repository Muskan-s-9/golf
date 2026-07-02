import { useEffect, useMemo, useState } from 'react';

const API_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [me, setMe] = useState(null);
  const [view, setView] = useState('home');
  const [charities, setCharities] = useState([]);
  const [scores, setScores] = useState([]);
  const [scoreInput, setScoreInput] = useState('');
  const [selectedCharity, setSelectedCharity] = useState('');
  const [charityPercent, setCharityPercent] = useState(10);
  const [donationAmount, setDonationAmount] = useState('0');
  const [donationNote, setDonationNote] = useState('');
  const [editScoreId, setEditScoreId] = useState('');
  const [editScoreValue, setEditScoreValue] = useState('');
  const [editScoreDate, setEditScoreDate] = useState('');
  const [authMode, setAuthMode] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [authMessage, setAuthMessage] = useState('');
  const [adminDashboard, setAdminDashboard] = useState(null);
  const [adminWinners, setAdminWinners] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminSubscriptions, setAdminSubscriptions] = useState([]);
  const [adminMessage, setAdminMessage] = useState('');
  const [drawEntryNumbers, setDrawEntryNumbers] = useState('');
  const [drawEntryQuantity, setDrawEntryQuantity] = useState(1);
  const [drawSimulation, setDrawSimulation] = useState(null);
  const [drawSummary, setDrawSummary] = useState(null);
  const [charityQuery, setCharityQuery] = useState('');
  const [charityCategoryFilter, setCharityCategoryFilter] = useState('');
  const [charityName, setCharityName] = useState('');
  const [charityDescription, setCharityDescription] = useState('');
  const [charityCategory, setCharityCategory] = useState('Community');
  const [charityLocation, setCharityLocation] = useState('');
  const [charityImageUrl, setCharityImageUrl] = useState('');
  const [charityActionMessage, setCharityActionMessage] = useState('');

  const isLoggedIn = useMemo(() => Boolean(token), [token]);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/me`, { headers: { 'x-token': token } }).then((r) => r.json()).then((data) => setMe(data));
    fetch(`${API_URL}/charities`).then((r) => r.json()).then((data) => setCharities(data));
    fetch(`${API_URL}/scores`, { headers: { 'x-token': token } }).then((r) => r.json()).then((data) => setScores(data));
    fetch(`${API_URL}/draws`, { headers: { 'x-token': token } }).then((r) => r.json()).then((data) => setDrawSummary(data));
  }, [token]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (charityQuery) params.set('q', charityQuery);
    if (charityCategoryFilter) params.set('category', charityCategoryFilter);
    fetch(`${API_URL}/charities?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => setCharities(data));
  }, [charityQuery, charityCategoryFilter]);

  useEffect(() => {
    if (!token || !me?.user?.role || me.user.role !== 'admin') return;
    fetch(`${API_URL}/admin/dashboard`, { headers: { 'x-token': token } })
      .then((r) => r.json())
      .then((data) => setAdminDashboard(data));
    fetch(`${API_URL}/admin/winners`, { headers: { 'x-token': token } })
      .then((r) => r.json())
      .then((data) => setAdminWinners(data));
    fetch(`${API_URL}/admin/users`, { headers: { 'x-token': token } })
      .then((r) => r.json())
      .then((data) => setAdminUsers(data));
    fetch(`${API_URL}/admin/subscriptions`, { headers: { 'x-token': token } })
      .then((r) => r.json())
      .then((data) => setAdminSubscriptions(data));
  }, [token, me]);

  const handleAuth = async (e) => {
    if (e) e.preventDefault();
    setAuthMessage('');

    if (!form.email.trim() || !form.password.trim()) {
      setAuthMessage('Please enter both email and password.');
      return;
    }

    const endpoint = authMode === 'login' ? '/login' : '/register';
    const payload = authMode === 'login' ? { email: form.email.trim(), password: form.password } : { ...form, email: form.email.trim(), full_name: form.full_name.trim() };

    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        data = {};
      }

      if (!res.ok) {
        setAuthMessage(data.detail || 'Unable to continue right now.');
        return;
      }

      if (data.token) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setMe({ user: data.user, subscription: { plan: 'monthly', status: 'active', charity_percentage: 10, renewal_date: null, donation_amount: 0, donation_note: '' }, scores: [], charity: null });
        setView('dashboard');
      } else {
        setAuthMessage('The server did not return an access token.');
      }
    } catch (error) {
      setAuthMessage('Could not reach the server. Please make sure the backend is running.');
    }
  };

  const handleScoreSubmit = async (e) => {
    e.preventDefault();
    if (!scoreInput) return;
    await fetch(`${API_URL}/scores`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ score: Number(scoreInput), score_date: new Date().toISOString().slice(0, 10) }),
    });
    const res = await fetch(`${API_URL}/scores`, { headers: { 'x-token': token } });
    const nextScores = await res.json();
    setScores(nextScores.slice(0, 5));
    setScoreInput('');
  };

  const handleSubscription = async () => {
    await fetch(`${API_URL}/subscription`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ plan: 'monthly', status: 'active', charity_percentage: Number(charityPercent), charity_id: Number(selectedCharity), donation_amount: Number(donationAmount || 0), donation_note: donationNote }),
    });
    const res = await fetch(`${API_URL}/me`, { headers: { 'x-token': token } });
    setMe(await res.json());
  };

  const updateScore = async (e) => {
    e.preventDefault();
    if (!editScoreId) return;
    await fetch(`${API_URL}/scores/${editScoreId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ score: Number(editScoreValue), score_date: editScoreDate }),
    });
    const res = await fetch(`${API_URL}/scores`, { headers: { 'x-token': token } });
    setScores(await res.json());
    setEditScoreId('');
    setEditScoreValue('');
    setEditScoreDate('');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setMe(null);
    setView('home');
  };

  const publishDraw = async () => {
    const res = await fetch(`${API_URL}/admin/draws/publish`, {
      method: 'POST',
      headers: { 'x-token': token },
    });
    const data = await res.json();
    setAdminMessage(data.message || 'Draw published');
    if (me?.user?.role === 'admin') {
      const dashboardRes = await fetch(`${API_URL}/admin/dashboard`, { headers: { 'x-token': token } });
      setAdminDashboard(await dashboardRes.json());
      const winnersRes = await fetch(`${API_URL}/admin/winners`, { headers: { 'x-token': token } });
      setAdminWinners(await winnersRes.json());
    }
  };

  const configureDraw = async (drawType) => {
    const res = await fetch(`${API_URL}/admin/draws/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ draw_type: drawType }),
    });
    const data = await res.json();
    setAdminMessage(data.message || 'Draw config updated');
  };

  const enterDraw = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API_URL}/draws/enter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ selected_numbers: drawEntryNumbers, quantity: drawEntryQuantity }),
    });
    const data = await res.json();
    setAdminMessage(data.message || 'Entry recorded');
    setDrawEntryNumbers('');
    setDrawEntryQuantity(1);
  };

  const simulateDraw = async () => {
    const res = await fetch(`${API_URL}/admin/draws/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ winning_numbers: drawEntryNumbers }),
    });
    const data = await res.json();
    setDrawSimulation(data);
  };

  const updateWinnerVerification = async (winnerId, status) => {
    const res = await fetch(`${API_URL}/admin/winners/${winnerId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ status }),
    });
    const data = await res.json();
    setAdminMessage(data.message || 'Verification updated');
    const winnersRes = await fetch(`${API_URL}/admin/winners`, { headers: { 'x-token': token } });
    setAdminWinners(await winnersRes.json());
  };

  const updateWinnerPayout = async (winnerId, status) => {
    const res = await fetch(`${API_URL}/admin/winners/${winnerId}/payout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-token': token },
      body: JSON.stringify({ status }),
    });
    const data = await res.json();
    setAdminMessage(data.message || 'Payout updated');
    const winnersRes = await fetch(`${API_URL}/admin/winners`, { headers: { 'x-token': token } });
    setAdminWinners(await winnersRes.json());
  };

  const refreshCharities = async () => {
    const res = await fetch(`${API_URL}/charities`);
    setCharities(await res.json());
  };

  const createCharity = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API_URL}/charities`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-token': token,
      },
      body: JSON.stringify({
        name: charityName,
        description: charityDescription,
        category: charityCategory,
        image_url: charityImageUrl,
        featured: false,
        location: charityLocation,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      setCharityActionMessage('Charity created successfully');
      setCharityName('');
      setCharityDescription('');
      setCharityCategory('Community');
      setCharityLocation('');
      setCharityImageUrl('');
      refreshCharities();
    } else {
      setCharityActionMessage(data.detail || 'Failed to create charity');
    }
  };

  const deleteCharity = async (id) => {
    const res = await fetch(`${API_URL}/charities/${id}`, {
      method: 'DELETE',
      headers: { 'x-token': token },
    });
    const data = await res.json();
    setCharityActionMessage(data.message || 'Charity deleted');
    refreshCharities();
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Golf impact platform</p>
          <h1>Turn every round into a meaningful draw.</h1>
          <p>Track scores, enter monthly prize draws, and support a charity with every subscription.</p>
          <div className="actions">
            <button onClick={() => { setView('dashboard'); if (!token) setAuthMode('login'); }}>Open app</button>
            <button className="secondary" onClick={() => setView('charities')}>Explore charities</button>
            {me?.user?.role === 'admin' && (
              <button className="secondary" onClick={() => setView('admin')}>Admin panel</button>
            )}
            {isLoggedIn ? (
              <button className="secondary" onClick={handleLogout}>Logout</button>
            ) : null}
          </div>
        </div>
      </header>

      <main className="content">
        {!isLoggedIn && view !== 'charities' && (
          <section className="card">
            <h2>Join the community</h2>
            <form onSubmit={handleAuth}>
              <div className="row">
                <button type="button" className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}>Login</button>
                <button type="button" className={authMode === 'register' ? 'active' : ''} onClick={() => setAuthMode('register')}>Register</button>
              </div>
              {authMode === 'register' && <input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />} 
              <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              {authMessage && <p>{authMessage}</p>}
              <button type="button" onClick={(e) => handleAuth(e)}>Continue</button>
            </form>
          </section>
        )}

        {isLoggedIn && view === 'dashboard' && me && (
          <section className="card">
            <h2>Welcome, {me.user.full_name}</h2>
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h3>Subscription status</h3>
                <p>Status: {me.subscription?.status || 'inactive'}</p>
                <p>Plan: {me.subscription?.plan || 'monthly'}</p>
                <p>Renewal date: {me.subscription?.renewal_date || 'Not set'}</p>
              </div>
              <div className="dashboard-card">
                <h3>Score entry</h3>
                <form onSubmit={handleScoreSubmit}>
                  <input value={scoreInput} onChange={(e) => setScoreInput(e.target.value)} placeholder="Enter Stableford score" />
                  <button type="submit">Save score</button>
                </form>
                <form onSubmit={updateScore}>
                  <select value={editScoreId} onChange={(e) => { const selected = scores.find((score) => score.id === Number(e.target.value)); setEditScoreId(e.target.value); setEditScoreValue(selected?.score || ''); setEditScoreDate(selected?.score_date || ''); }}>
                    <option value="">Select score to edit</option>
                    {scores.map((score) => <option key={score.id} value={score.id}>{score.score} — {score.score_date}</option>)}
                  </select>
                  <input value={editScoreValue} onChange={(e) => setEditScoreValue(e.target.value)} placeholder="Updated score" />
                  <input type="date" value={editScoreDate} onChange={(e) => setEditScoreDate(e.target.value)} />
                  <button type="submit">Update score</button>
                </form>
                <p>Latest 5 scores only are retained. New entries replace the oldest automatically.</p>
                <ul>
                  {scores.slice().sort((a, b) => new Date(b.score_date) - new Date(a.score_date)).map((score) => <li key={score.id}>{score.score} on {score.score_date}</li>)}
                </ul>
              </div>
              <div className="dashboard-card">
                <h3>Selected charity</h3>
                <p>Current charity: {me.charity?.name || 'No charity selected yet'}</p>
                <select value={selectedCharity} onChange={(e) => setSelectedCharity(e.target.value)}>
                  <option value="">Select a charity</option>
                  {charities.map((charity) => <option key={charity.id} value={charity.id}>{charity.name}</option>)}
                </select>
                <input type="number" min="10" max="100" value={charityPercent} onChange={(e) => setCharityPercent(e.target.value)} placeholder="Contribution %" />
                <input type="number" min="0" step="0.01" value={donationAmount} onChange={(e) => setDonationAmount(e.target.value)} placeholder="Independent donation" />
                <input value={donationNote} onChange={(e) => setDonationNote(e.target.value)} placeholder="Donation note" />
                <button onClick={handleSubscription}>Save impact preference</button>
                <p>Minimum charity contribution is 10% of the subscription fee. You can also add an independent donation.</p>
              </div>
              <div className="dashboard-card">
                <h3>Participation summary</h3>
                <p>Draws entered: {scores.length > 0 ? '1 current draw entry' : 'No draw entries yet'}</p>
                <p>Upcoming draws: Monthly draw open for the current month</p>
              </div>
            </div>
          </section>
        )}

        {view === 'charities' && (
          <section className="card">
            <h2>Charity directory</h2>
            <div className="charity-filters">
              <input value={charityQuery} onChange={(e) => setCharityQuery(e.target.value)} placeholder="Search charities" />
              <input value={charityCategoryFilter} onChange={(e) => setCharityCategoryFilter(e.target.value)} placeholder="Filter by category" />
            </div>
            {charities.filter((charity) => charity.featured).length > 0 && (
              <div className="dashboard-card">
                <h3>Spotlight charity</h3>
                {charities.filter((charity) => charity.featured).slice(0, 1).map((charity) => (
                  <div key={charity.id}>
                    <strong>{charity.name}</strong>
                    <p>{charity.description}</p>
                    <p>{charity.upcoming_events}</p>
                  </div>
                ))}
              </div>
            )}
            {charities.map((charity) => (
              <div key={charity.id} className="charity-item">
                <strong>{charity.name}</strong>
                <p>{charity.description}</p>
                <p>Category: {charity.category} • Location: {charity.location}</p>
                <p>Upcoming events: {charity.upcoming_events || 'No events announced yet'}</p>
              </div>
            ))}
          </section>
        )}

        {view === 'admin' && me?.user?.role === 'admin' && (
          <section className="card">
            <h2>Admin dashboard</h2>
            <p>Welcome, {me.user.full_name}. Use this panel to publish draws and review winners.</p>
            <button onClick={publishDraw}>Publish monthly draw</button>
            {adminMessage && <p>{adminMessage}</p>}
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h3>Metrics</h3>
                <p>Total users: {adminDashboard?.total_users ?? '–'}</p>
                <p>Active subscriptions: {adminDashboard?.active_subscriptions ?? '–'}</p>
                <p>Total charities: {adminDashboard?.total_charities ?? '–'}</p>
                <p>Total winners: {adminDashboard?.total_winners ?? '–'}</p>
                <p>Total prize pool: {adminDashboard?.total_prize_pool ?? '–'}</p>
                <p>Charity contribution total: {adminDashboard?.charity_contribution_total ?? '–'}</p>
                <p>Current draw status: {adminDashboard?.current_draw?.status ?? '–'}</p>
                <p>Current draw month: {adminDashboard?.current_draw?.month ?? '–'}</p>
              </div>
              <div className="dashboard-card">
                <h3>Draw configuration</h3>
                <p>Supported tiers: 5-number match, 4-number match, 3-number match.</p>
                <p>Monthly cadence: one draw is published each month.</p>
                <p>Prize pool tiers: 5-match 40%, 4-match 35%, 3-match 25%.</p>
                <p>Jackpot rolls over when no 5-match winner is found.</p>
                <button onClick={() => configureDraw('random')}>Random draw</button>
                <button onClick={() => configureDraw('algorithm')}>Algorithmic draw</button>
                <button onClick={publishDraw}>Publish monthly draw</button>
                {adminMessage && <p>{adminMessage}</p>}
              </div>
              <div className="dashboard-card">
                <h3>Draw controls</h3>
                <form onSubmit={enterDraw}>
                  <input value={drawEntryNumbers} onChange={(e) => setDrawEntryNumbers(e.target.value)} placeholder="5-digit entry" />
                  <input type="number" min="1" max="10" value={drawEntryQuantity} onChange={(e) => setDrawEntryQuantity(Number(e.target.value))} placeholder="Quantity" />
                  <button type="submit">Enter draw</button>
                </form>
                <button onClick={simulateDraw}>Simulate draw</button>
                {drawSummary && (
                  <div>
                    <p>Current draw: {drawSummary.draw?.month} {drawSummary.draw?.year}</p>
                    <p>Status: {drawSummary.draw?.status}</p>
                    <p>Draw type: {drawSummary.draw?.draw_type}</p>
                    <p>Jackpot: {drawSummary.draw?.jackpot}</p>
                    <p>Total pool: {drawSummary.draw?.total_pool}</p>
                  </div>
                )}
                {drawSimulation && (
                  <div>
                    <p>Winning numbers: {drawSimulation.winning_numbers}</p>
                    <ul>
                      {drawSimulation.results.map((result, index) => (
                        <li key={index}>{result.full_name} — {result.tier} — {result.matches} matches</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div className="dashboard-card">
                <h3>Recent winners</h3>
                {adminWinners.length === 0 ? (
                  <p>No winners found</p>
                ) : (
                  <ul>
                    {adminWinners.map((winner) => (
                      <li key={winner.id}>
                        {winner.full_name} — {winner.prize_tier} — ${winner.amount} — {winner.verification_status}
                        <div className="inline-actions">
                          <button type="button" onClick={() => updateWinnerVerification(winner.id, 'approved')}>Approve</button>
                          <button type="button" onClick={() => updateWinnerVerification(winner.id, 'rejected')}>Reject</button>
                          <button type="button" onClick={() => updateWinnerPayout(winner.id, 'paid')}>Mark paid</button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h3>User management</h3>
                {adminUsers.length === 0 ? <p>No users found</p> : <ul>{adminUsers.map((user) => <li key={user.id}>{user.full_name} ({user.email}) — {user.role}</li>)}</ul>}
              </div>
              <div className="dashboard-card">
                <h3>Subscription management</h3>
                {adminSubscriptions.length === 0 ? <p>No subscriptions found</p> : <ul>{adminSubscriptions.map((subscription) => <li key={subscription.id}>{subscription.user_id} — {subscription.plan} — {subscription.status} — {subscription.charity_percentage}%</li>)}</ul>}
              </div>
              <div className="dashboard-card">
                <h3>Create charity</h3>
                <form onSubmit={createCharity}>
                  <input value={charityName} onChange={(e) => setCharityName(e.target.value)} placeholder="Charity name" />
                  <input value={charityCategory} onChange={(e) => setCharityCategory(e.target.value)} placeholder="Category" />
                  <input value={charityLocation} onChange={(e) => setCharityLocation(e.target.value)} placeholder="Location" />
                  <input value={charityImageUrl} onChange={(e) => setCharityImageUrl(e.target.value)} placeholder="Image URL" />
                  <textarea value={charityDescription} onChange={(e) => setCharityDescription(e.target.value)} placeholder="Description" rows={3} />
                  <button type="submit">Create charity</button>
                </form>
                {charityActionMessage && <p>{charityActionMessage}</p>}
              </div>
              <div className="dashboard-card">
                <h3>Charity management</h3>
                {charities.length === 0 ? (
                  <p>No charities available</p>
                ) : (
                  <ul>
                    {charities.map((charity) => (
                      <li key={charity.id}>
                        <strong>{charity.name}</strong>
                        <div>{charity.category} • {charity.location}</div>
                        <button type="button" onClick={() => deleteCharity(charity.id)}>Delete</button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;

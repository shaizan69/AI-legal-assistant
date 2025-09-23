import React, { useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from 'react-query';
import { MessageSquare, Plus } from 'lucide-react';
import { qaAPI } from '../api/qa';

const QAPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const { data: sessions = [], isLoading } = useQuery(
    ['qa-sessions-list'],
    () => qaAPI.getSessions(),
    { refetchOnWindowFocus: false }
  );

  // If navigated with ?document=ID, create a session and redirect to it
  useEffect(() => {
    const docId = searchParams.get('document');
    if (!docId) return;
    (async () => {
      try {
        const session = await qaAPI.createSession(Number(docId));
        // refresh list cache
        queryClient.invalidateQueries(['qa-sessions-list']);
        navigate(`/qa/${session.id}`, { replace: true });
      } catch (e) {
        console.error('Failed to create session from document param', e);
        alert('Unable to start Q&A session. Ensure the document has finished processing.');
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="qa-page" style={{padding: '1.5rem'}}>
      <div className="section-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
        <h1 className="section-title">Q&A Sessions</h1>
        <div style={{opacity: 0.6, fontSize: 14}}>{sessions.length} sessions</div>
      </div>

      {isLoading ? (
        <div>Loading sessions…</div>
      ) : sessions.length === 0 ? (
        <div className="empty-state" style={{textAlign: 'center', padding: '3rem', background: '#fafafa', borderRadius: 8}}>
          <MessageSquare size={48} className="empty-icon" />
          <h3>No Q&A sessions yet</h3>
          <p>Open a document and click Start Q&A to begin.</p>
        </div>
      ) : (
        <div className="sessions-list" style={{display: 'grid', gap: '0.75rem'}}>
          {sessions.map((s) => (
            <div key={s.id} className="session-item" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', border: '1px solid #e5e7eb', borderRadius: 8}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                <MessageSquare size={20} />
                <div>
                  <div style={{fontWeight: 600}}>{s.session_name}</div>
                  <div style={{fontSize: 12, color: '#6b7280'}}>{s.total_questions} questions • {s.is_active ? 'Active' : 'Inactive'}</div>
                </div>
              </div>
              <Link to={`/qa/${s.id}`} className="btn btn-sm btn-outline">Open</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default QAPage;



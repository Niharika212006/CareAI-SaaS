import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Users,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';

export function HomePage() {
  const { isAuthenticated, role } = useAuth();

  const getDashboardLink = () => {
    if (role === 'DOCTOR') return '/doctor/dashboard';
    if (role === 'ADMIN') return '/admin/dashboard';
    return '/patient/dashboard';
  };

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <section
        style={{
          background: 'linear-gradient(180deg, rgba(20, 184, 166, 0.08) 0%, rgba(248, 250, 252, 1) 100%)',
          padding: '5rem 1.5rem 4rem 1.5rem',
          textAlign: 'center',
        }}
      >
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ display: 'inline-flex', marginBottom: '1.25rem' }}>
            <Badge variant="teal" style={{ padding: '0.375rem 0.875rem', fontSize: '0.8125rem' }}>
              <Sparkles size={14} style={{ marginRight: '4px' }} /> Clinical AI Decision Support Engine
            </Badge>
          </div>

          <h1
            style={{
              fontSize: '3rem',
              lineHeight: 1.15,
              marginBottom: '1.5rem',
              fontWeight: 800,
              background: 'linear-gradient(135deg, var(--secondary-900) 0%, var(--primary-700) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Intelligent AI Healthcare SaaS Platform
          </h1>

          <p style={{ fontSize: '1.125rem', color: 'var(--secondary-500)', marginBottom: '2.5rem', lineHeight: 1.6 }}>
            Empowering Patients, Doctors, and Clinical Administrators with seamless digital workflows,
            verified doctor discovery, and real-time AI drug interaction analysis.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {isAuthenticated ? (
              <Link to={getDashboardLink()} className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
                Go to My Dashboard <ArrowRight size={18} />
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
                  Register as Patient / Doctor <ArrowRight size={18} />
                </Link>
                <Link to="/login" className="btn btn-secondary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
                  Sign In to Portal
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Role-Based Overview Grid */}
      <section className="page-container" style={{ paddingBottom: '4rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Architected for Every Healthcare Stakeholder</h2>
          <p style={{ color: 'var(--secondary-500)' }}>
            Role-Based Access Control ensures each user accesses a purpose-built workspace.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Patient Card */}
          <Card hover className="glass-panel">
            <div style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Users size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>For Patients</h3>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Manage your personal health profile, browse verified doctors, schedule consultations, and view AI-reviewed prescriptions.
            </p>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="var(--primary-600)" /> Health History & Allergies
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="var(--primary-600)" /> Verified Doctor Discovery
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="var(--primary-600)" /> Digital Prescription Vault
              </li>
            </ul>
          </Card>

          {/* Doctor Card */}
          <Card hover className="glass-panel">
            <div style={{ background: '#e0f2fe', color: '#0369a1', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Stethoscope size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>For Doctors</h3>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Submit license credentials for approval, manage appointment slots, author digital prescriptions, and run AI safety checks.
            </p>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#0369a1" /> Credentialed Profile & Verification
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#0369a1" /> Digital Prescription Generator
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#0369a1" /> Real-time Interaction Analysis
              </li>
            </ul>
          </Card>

          {/* Admin Card */}
          <Card hover className="glass-panel">
            <div style={{ background: '#ffe4e6', color: '#be123c', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <ShieldCheck size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>For Administrators</h3>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Review doctor credentials, manage user permissions, monitor system health, and oversee clinical safety audits.
            </p>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#be123c" /> Doctor Approval Workflow
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#be123c" /> System-wide Audit & User Management
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} color="#be123c" /> Clinical Analytics & Logs
              </li>
            </ul>
          </Card>
        </div>
      </section>

      {/* AI Drug Safety Feature Highlight */}
      <section style={{ background: '#ffffff', borderTop: '1px solid var(--secondary-200)', padding: '4rem 1.5rem' }}>
        <div className="page-container" style={{ display: 'flex', alignItems: 'center', gap: '3rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 400px' }}>
            <Badge variant="teal" style={{ marginBottom: '1rem' }}>Clinical Safety Innovation</Badge>
            <h2 style={{ fontSize: '2.25rem', lineHeight: 1.2, marginBottom: '1rem' }}>
              Multi-Dimensional AI Prescription Analyzer
            </h2>
            <p style={{ color: 'var(--secondary-500)', marginBottom: '1.5rem' }}>
              Our hybrid clinical rule and LLM engine instantly evaluates medication combinations across three critical vectors to prevent adverse drug events.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <AlertTriangle size={20} color="var(--accent-rose)" />
                <div>
                  <strong>Drug-Drug Interactions (DDI):</strong> Detects pharmacological contraindications and elevated toxicity risks.
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Activity size={20} color="var(--accent-amber)" />
                <div>
                  <strong>Drug-Food Interactions (DFI):</strong> Identifies nutrient chelation and meal-timing restrictions.
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <ShieldCheck size={20} color="var(--accent-emerald)" />
                <div>
                  <strong>Drug-Allergy Interactions (DAI):</strong> Cross-references prescribed items with patient hypersensitivity records.
                </div>
              </div>
            </div>
          </div>

          <div style={{ flex: '1 1 400px' }}>
            <Card className="glass-panel" style={{ border: '1px solid var(--primary-200)', background: 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,253,250,0.8))' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>AI Clinical Safety Report</span>
                <Badge variant="rose">High Alert</Badge>
              </div>
              <div style={{ fontSize: '0.875rem', marginBottom: '1rem', color: 'var(--secondary-700)' }}>
                <strong>Combination:</strong> Aspirin 100mg + Warfarin 5mg
              </div>
              <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '8px', padding: '0.75rem', fontSize: '0.8125rem', color: '#9f1239', marginBottom: '1rem' }}>
                ⚠️ <strong>High Risk:</strong> Concurrent anticoagulant and antiplatelet therapy significantly increases gastrointestinal bleeding hazard.
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                💡 <em>AI Recommendation: Consider proton-pump inhibitor co-prescription or dosage recalibration.</em>
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}

export default HomePage;

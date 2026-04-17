
import React, { useEffect, useState, useMemo, useRef } from 'react';
import { Screen, Transaction, Budget } from '../types';
import { MOCK_PRODUCTS } from '../constants';
import { Header, Button, Input } from '../components/Shared';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { analytics, reports } from '../api';
import { Sparkles, RefreshCw, TrendingUp, AlertTriangle, PieChart as PieIcon, BarChart as BarIcon, Activity, Plus, Edit2, X, AlertCircle, ShoppingCart, Repeat, Users, Loader2, Save, Download } from 'lucide-react';

interface Props {
  onNavigate: (screen: Screen) => void;
  onToggleMenu: () => void;
  isDarkMode: boolean;
  transactions: Transaction[];
}

import { useAnalytics, useBudgets, useTransactionSummary, useProducts } from '../hooks';

const DashboardScreen: React.FC<Props> = ({ onNavigate, onToggleMenu, isDarkMode, transactions }) => {
  const { overview, breakdown, kpi, activity, loading: analyticsLoading } = useAnalytics();
  const { data: budgets, loading: budgetsLoading, addBudget, updateBudget, deleteBudget, refetch: refetchBudgets } = useBudgets();
  const { summary, loading: summaryLoading } = useTransactionSummary();
  const { data: products } = useProducts();

  const [insights, setInsights] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDownloadingSyscohada, setIsDownloadingSyscohada] = useState(false);

  // Budget State
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [newBudgetCategory, setNewBudgetCategory] = useState('');
  const [newBudgetLimit, setNewBudgetLimit] = useState('');

  // Use backend data if available, otherwise fallback to empty or mock for display safety
  const DATA_OVERVIEW = overview.length > 0 ? overview.map(item => ({
    name: item.month,
    revenus: parseFloat(item.income),
    depenses: parseFloat(item.expenses)
  })) : [];

  const DATA_CATEGORIES = breakdown.length > 0 ? breakdown.map(item => ({
    name: item.category,
    value: parseFloat(item.amount)
  })) : [];

  const COLORS = ['#14532d', '#34d399', '#f59e0b', '#ef4444', '#60a5fa', '#8b5cf6'];

  // Weekly data is not yet provided by backend, keep mock or implement endpoint
  // Weekly data from backend
  const DATA_WEEKLY = activity.length > 0 ? activity.map(item => ({
    day: item.day,
    sales: parseFloat(item.sales)
  })) : [
    { day: 'Lun', sales: 0 },
    { day: 'Mar', sales: 0 },
    { day: 'Mer', sales: 0 },
    { day: 'Jeu', sales: 0 },
    { day: 'Ven', sales: 0 },
    { day: 'Sam', sales: 0 },
    { day: 'Dim', sales: 0 },
  ];

  // KPIs Calculations from backend
  const avgTransactionValue = kpi?.average_basket ? parseFloat(kpi.average_basket) : 0;
  const avgTransactionValueGrowth = kpi?.average_basket_growth || 0;
  const mrr = kpi?.estimated_mrr ? parseFloat(kpi.estimated_mrr) : 0;
  const mrrGrowth = kpi?.estimated_mrr_growth || 0;
  const cac = kpi?.cac ? parseFloat(kpi.cac) : 0;
  const cacGrowth = kpi?.cac_growth || 0;

  const profitMargin = useMemo(() => {
    const totalIncome = DATA_OVERVIEW.reduce((acc, item) => acc + item.revenus, 0);
    const totalExpenses = DATA_OVERVIEW.reduce((acc, item) => acc + item.depenses, 0);
    if (totalIncome === 0) return 0;
    return ((totalIncome - totalExpenses) / totalIncome * 100).toFixed(1);
  }, [DATA_OVERVIEW]);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      // Construct context from passed transactions
      const contextData = {
        transactions: transactions.slice(0, 10).map(t => ({ name: t.name, amount: t.amount, type: t.type, category: t.category })),
        products: (products.length > 0 ? products : MOCK_PRODUCTS).map(p => ({ name: p.name, stock: p.stockStatus, category: p.category }))
      };

      const response = await analytics.insights(contextData);
      const items = response.data.insights || [];

      setInsights(items.length > 0 ? items : ["Analyse des ventes en cours...", "Vérification des stocks...", "Calcul des marges..."]);

    } catch (error) {
      console.error("AI Error:", error);
      setInsights([
        "Les ventes de Tomates sont en hausse de 18%.",
        "Attention, dépense élevée détectée (Télévision).",
        "Stock de Mais critique, pensez à ravitailler."
      ]);
    } finally {
      setLoading(false);
    }
  };

  const downloadSyscohadaReports = async () => {
    if (isDownloadingSyscohada) return;
    setIsDownloadingSyscohada(true);
    try {
      const year = new Date().getFullYear();
      const res = await reports.syscohadaZip(year);
      const blob = new Blob([res.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);

      const disposition = (res.headers && (res.headers['content-disposition'] || res.headers['Content-Disposition'])) as string | undefined;
      const match = disposition?.match(/filename=\"?([^\";]+)\"?/i);
      const filename = match?.[1] || `rapports_syscohada_${year}.zip`;

      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download SYSCOHADA reports', e);
      alert("Impossible de télécharger les rapports SYSCOHADA pour le moment.");
    } finally {
      setIsDownloadingSyscohada(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [transactions]);

  // Helper to calculate spent amount per category
  const getSpentAmount = (category: string) => {
    return transactions
      .filter(t => t.type === 'expense' && (t.category?.toLowerCase() === category.toLowerCase() || (!t.category && category === 'Divers')))
      .reduce((sum, t) => sum + t.amount, 0);
  };

  const handleSaveBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBudgetCategory || !newBudgetLimit || isSaving) return;

    setIsSaving(true);
    try {
      const limit = parseFloat(newBudgetLimit);

      if (editingBudget) {
        // Update logic
        if (editingBudget.id) {
          await updateBudget(editingBudget.id, {
            category: newBudgetCategory,
            limit
          });
        }
      } else {
        await addBudget({
          category: newBudgetCategory,
          limit,
          color: '#' + Math.floor(Math.random() * 16777215).toString(16)
        });
      }

      closeBudgetModal();
    } catch (error) {
      console.error("Error saving budget:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const openEditBudget = (budget: Budget) => {
    setEditingBudget(budget);
    setNewBudgetCategory(budget.category);
    setNewBudgetLimit(budget.limit.toString());
    setIsBudgetModalOpen(true);
  };

  const openNewBudget = () => {
    setEditingBudget(null);
    setNewBudgetCategory('');
    setNewBudgetLimit('');
    setIsBudgetModalOpen(true);
  };

  const closeBudgetModal = () => {
    setIsBudgetModalOpen(false);
    setEditingBudget(null);
  };

  const handleDeleteBudget = async () => {
    if (editingBudget) {
      await deleteBudget(editingBudget.id);
      closeBudgetModal();
    }
  }

  // Theme constants
  const chartTextColor = isDarkMode ? '#9ca3af' : '#9ca3af';
  const chartGridColor = isDarkMode ? '#374151' : '#f0fdf4';
  const tooltipBg = isDarkMode ? '#1f2937' : '#fff';
  const tooltipBorder = isDarkMode ? '#374151' : 'none';
  const tooltipText = isDarkMode ? '#e5e7eb' : '#333';

  return (
    <div className="flex flex-col h-full bg-[#dbece5] dark:bg-gray-900 pb-24 overflow-y-auto no-scrollbar transition-colors">
      {/* Standard Header */}
      <Header
        showProfile
        onMenu={onToggleMenu}
        title=""
      />

      {/* Quick Filters */}
      <div className="px-6 flex gap-2 overflow-x-auto no-scrollbar mb-4">
        {['Vente', 'Produit', 'Dépense', 'Stock'].map((filter) => (
          <button key={filter} className="px-4 py-1.5 bg-white/50 dark:bg-gray-800/50 rounded-full text-primary dark:text-green-400 font-medium text-xs hover:bg-white dark:hover:bg-gray-700 transition-colors">
            {filter}
          </button>
        ))}
      </div>

      <div className="px-6">
        <div className="flex justify-between items-end mb-6">
          <h1 className="text-3xl font-bold text-primary dark:text-white">Tableau de bord</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadSyscohadaReports}
              className={`p-2 bg-primary/10 dark:bg-green-400/10 rounded-full text-primary dark:text-green-400 hover:bg-primary hover:text-white transition-colors ${isDownloadingSyscohada ? 'opacity-60 cursor-not-allowed' : ''}`}
              title="Télécharger les rapports SYSCOHADA"
              disabled={isDownloadingSyscohada}
            >
              {isDownloadingSyscohada ? <Loader2 size={20} className="animate-spin" /> : <Download size={20} />}
            </button>
            <button
              onClick={fetchInsights}
              className={`p-2 bg-primary/10 dark:bg-green-400/10 rounded-full text-primary dark:text-green-400 hover:bg-primary hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
              title="Rafraîchir les insights"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>

        {/* Chart 1: Revenue vs Expenses (Bar Chart) */}
        <div className="bg-white dark:bg-gray-800 rounded-[30px] p-5 shadow-sm mb-6 transition-colors">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-primary dark:text-green-400 flex items-center gap-2">
              <BarIcon size={18} /> Revenus vs Dépenses
            </h3>
            <select className="bg-gray-100 dark:bg-gray-700 text-xs rounded-lg px-2 py-1 outline-none text-gray-600 dark:text-gray-300 border-none cursor-pointer transition-colors">
              <option>6 derniers mois</option>
              <option>Cette année</option>
            </select>
          </div>
          <div className="h-52 w-full min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DATA_OVERVIEW} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={chartGridColor} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: chartTextColor, fontSize: 10 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: chartTextColor, fontSize: 10 }} />
                <Tooltip
                  cursor={{ fill: isDarkMode ? '#374151' : '#f0fdf4' }}
                  contentStyle={{
                    borderRadius: '16px',
                    border: tooltipBorder,
                    backgroundColor: tooltipBg,
                    color: tooltipText,
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '12px', color: chartTextColor }} />
                <Bar dataKey="revenus" name="Revenus" fill="#14532d" radius={[6, 6, 0, 0]} barSize={12} />
                <Bar dataKey="depenses" name="Dépenses" fill="#34d399" radius={[6, 6, 0, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Analytics Section */}
        <div className="mb-6 bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-[30px] p-5 border border-white/50 dark:border-gray-700 shadow-sm transition-colors">
          <div className="flex items-center gap-2 mb-4 text-primary dark:text-green-400">
            <Sparkles size={20} className="fill-current" />
            <h3 className="font-bold text-lg">Akompta Insights</h3>
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-4 bg-primary/10 dark:bg-green-400/10 rounded w-3/4"></div>
                <div className="h-4 bg-primary/10 dark:bg-green-400/10 rounded w-full"></div>
                <div className="h-4 bg-primary/10 dark:bg-green-400/10 rounded w-5/6"></div>
              </div>
            ) : (
              insights.map((insight, idx) => (
                <div key={idx} className="flex gap-3 items-start">
                  <div className={`mt-1 min-w-[16px] h-4 rounded-full flex items-center justify-center ${idx === 2 ? 'text-orange-600 dark:text-orange-400' : 'text-primary dark:text-green-400'}`}>
                    {idx === 0 && <TrendingUp size={16} />}
                    {idx === 1 && <div className="w-2 h-2 bg-primary dark:bg-green-400 rounded-full" />}
                    {idx === 2 && <AlertTriangle size={16} />}
                  </div>
                  <p className="text-sm text-primary/80 dark:text-gray-300 leading-tight font-medium">{insight.replace(/^- /, '')}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* KPIs Section (NEW) */}
        <div className="bg-white dark:bg-gray-800 rounded-[30px] p-5 shadow-sm mb-6 transition-colors">
          <h3 className="font-bold text-primary dark:text-green-400 mb-4 flex items-center gap-2">
            <Activity size={18} /> Performance
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {/* ATV Card */}
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-2xl flex flex-col justify-between h-24 relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <ShoppingCart size={32} />
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wide">Panier Moyen</div>
              <div>
                <div className="text-lg font-bold text-primary dark:text-white leading-none mb-1">{avgTransactionValue.toLocaleString()}</div>
                <div className={`text-[9px] font-bold ${avgTransactionValueGrowth >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {avgTransactionValueGrowth >= 0 ? '+' : ''}{avgTransactionValueGrowth.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* MRR Card */}
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-2xl flex flex-col justify-between h-24 relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Repeat size={32} />
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wide">MRR (Est.)</div>
              <div>
                <div className="text-lg font-bold text-primary dark:text-white leading-none mb-1">{mrr.toLocaleString()}</div>
                <div className={`text-[9px] font-bold ${mrrGrowth >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {mrrGrowth >= 0 ? '+' : ''}{mrrGrowth.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* CAC Card */}
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-2xl flex flex-col justify-between h-24 relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Users size={32} />
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wide">Coût Acq.</div>
              <div>
                <div className="text-lg font-bold text-primary dark:text-white leading-none mb-1">{cac.toLocaleString()}</div>
                <div className={`text-[9px] font-bold ${cacGrowth <= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {cacGrowth > 0 ? '+' : ''}{cacGrowth.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Budget Tracking Section */}
        <div className="bg-white dark:bg-gray-800 rounded-[30px] p-5 shadow-sm mb-6 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-primary dark:text-green-400 flex items-center gap-2">
              <Activity size={18} /> Suivi Budgétaire
            </h3>
            <button
              onClick={openNewBudget}
              className="p-1.5 bg-primary/10 dark:bg-white/10 text-primary dark:text-green-400 rounded-full hover:bg-primary hover:text-white transition-colors"
            >
              <Plus size={16} />
            </button>
          </div>

          <div className="space-y-4">
            {budgets.map(budget => {
              const spent = parseFloat(budget.spent_amount?.toString() || '0');
              const percentage = budget.percentage || 0;
              let colorClass = 'bg-green-500';
              if (percentage > 50) colorClass = 'bg-yellow-500';
              if (percentage > 80) colorClass = 'bg-red-500';

              return (
                <div key={budget.id} className="cursor-pointer group" onClick={() => openEditBudget(budget)}>
                  <div className="flex justify-between text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    <span>{budget.category}</span>
                    <span>{spent.toLocaleString()} / {budget.limit.toLocaleString()} F</span>
                  </div>
                  <div className="h-2 w-full bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                  {percentage >= 90 && (
                    <div className="flex items-center gap-1 text-[10px] text-red-500 mt-1 font-medium">
                      <AlertCircle size={10} /> Attention, budget presque atteint
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex gap-4 mb-6">
          {/* Chart 2: Categories (Pie Chart) */}
          <div className="bg-white dark:bg-gray-800 rounded-[30px] p-4 shadow-sm flex-1 flex flex-col transition-colors">
            <h3 className="font-bold text-primary dark:text-green-400 text-sm mb-2 flex items-center gap-2">
              <PieIcon size={16} /> Dépenses
            </h3>
            <div className="h-32 relative flex-1 min-h-[120px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={DATA_CATEGORIES}
                    cx="50%"
                    cy="50%"
                    innerRadius={25}
                    outerRadius={45}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {DATA_CATEGORIES.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: tooltipBorder,
                      backgroundColor: tooltipBg,
                      color: tooltipText,
                      fontSize: '10px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="text-[10px] font-bold text-gray-400">Total</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-x-2 gap-y-1 mt-2 justify-center">
              {DATA_CATEGORIES.map((cat, idx) => (
                <div key={idx} className="flex items-center gap-1 text-[9px] text-gray-500 dark:text-gray-400 font-medium">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: COLORS[idx] }}></div>
                  {cat.name}
                </div>
              ))}
            </div>
          </div>

          {/* Chart 3: Weekly Activity (Area Chart) */}
          <div className="bg-white dark:bg-gray-800 rounded-[30px] p-4 shadow-sm flex-1 flex flex-col transition-colors">
            <h3 className="font-bold text-primary dark:text-green-400 text-sm mb-2 flex items-center gap-2">
              <Activity size={16} /> Activité
            </h3>
            <div className="flex-1 min-h-[80px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={DATA_WEEKLY}>
                  <defs>
                    <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Tooltip
                    contentStyle={{
                      fontSize: '10px',
                      borderRadius: '8px',
                      border: tooltipBorder,
                      backgroundColor: tooltipBg,
                      color: tooltipText
                    }}
                    itemStyle={{ color: '#f59e0b' }}
                  />
                  <Area type="monotone" dataKey="sales" stroke="#f59e0b" fillOpacity={1} fill="url(#colorSales)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center mt-auto">
              <div className="text-lg font-bold text-primary dark:text-white transition-colors">+24%</div>
              <div className="text-[10px] text-gray-400">cette semaine</div>
            </div>
          </div>
        </div>

        {/* Profit Margin Card */}
        <div className="bg-primary rounded-[30px] p-6 text-white shadow-lg shadow-primary/30 relative overflow-hidden mb-6">
          <div className="relative z-10 flex justify-between items-end">
            <div>
              <div className="text-sm opacity-80 mb-1 font-medium">Marge Bénéficiaire</div>
              <div className="text-4xl font-bold">{profitMargin}%</div>
            </div>
            <div className="h-12 w-24">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={DATA_OVERVIEW}>
                  <Line type="monotone" dataKey="revenus" stroke="#ffffff" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          {/* Decorative background elements */}
          <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-accent/20 rounded-full blur-xl"></div>
        </div>
      </div>

      {/* Budget Modal */}
      {isBudgetModalOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity" onClick={closeBudgetModal}></div>

          {/* Modal Content */}
          <div className="bg-white dark:bg-gray-800 w-full max-w-sm rounded-[30px] p-6 relative z-10 shadow-2xl animate-in zoom-in-95 duration-200">
            <button
              onClick={closeBudgetModal}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full text-gray-500 dark:text-gray-300 transition-colors"
            >
              <X size={18} />
            </button>

            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-6 text-center">
              {editingBudget ? 'Modifier le budget' : 'Nouveau budget'}
            </h3>

            <form onSubmit={handleSaveBudget} className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Catégorie</label>
                <select
                  value={newBudgetCategory}
                  onChange={(e) => setNewBudgetCategory(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                >
                  <option value="" disabled>Sélectionner...</option>
                  <option value="Transport">Transport</option>
                  <option value="Stock">Stock</option>
                  <option value="Loyer">Loyer</option>
                  <option value="Electricité">Electricité</option>
                  <option value="Eau">Eau</option>
                  <option value="Equipement">Equipement</option>
                  <option value="Salaires">Salaires</option>
                  <option value="Divers">Divers</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Limite (FCFA)</label>
                <input
                  type="number"
                  value={newBudgetLimit}
                  onChange={(e) => setNewBudgetLimit(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-bold text-lg"
                  placeholder="0"
                />
              </div>

              <div className="flex gap-3 w-full mt-8">
                {editingBudget && (
                  <button
                    type="button"
                    onClick={handleDeleteBudget}
                    className="px-4 py-3.5 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 font-bold text-sm hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                  >
                    <X size={20} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={closeBudgetModal}
                  className="flex-1 py-3.5 rounded-2xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-bold text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 py-3.5 rounded-2xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/30 hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  {isSaving ? 'Enregistrement...' : 'Enregistrer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardScreen;

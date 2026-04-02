
import React, { useState, useMemo } from 'react';
import { Screen, Transaction } from '../types';
import { Header, Button } from '../components/Shared';
import { ChevronDown, ArrowUpRight, ArrowDownLeft, Wallet, Calendar, X, Share2, FileText, Printer, Search, Plus, Save, Minus, Loader2 } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { useAnalytics, useTransactionSummary } from '../hooks';

interface Props {
  onNavigate: (screen: Screen) => void;
  transactions: Transaction[];
  onToggleMenu: () => void;
  isDarkMode: boolean;
  onAddTransaction: (tx: Omit<Transaction, 'id'>) => void;
}

const WalletScreen: React.FC<Props> = ({ onNavigate, transactions, onToggleMenu, isDarkMode, onAddTransaction }) => {
  const { balanceHistory, loading: analyticsLoading, refetch: refetchAnalytics } = useAnalytics();
  const { summary, loading: summaryLoading, refetch: refetchSummary } = useTransactionSummary();
  const [isSaving, setIsSaving] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [timeRange, setTimeRange] = useState<'Jour' | 'Semaine' | 'Mois' | 'Année'>('Mois');

  // Transaction Modal State (Income/Expense)
  const [activeModal, setActiveModal] = useState<'income' | 'expense' | null>(null);
  const [txName, setTxName] = useState('');
  const [txAmount, setTxAmount] = useState('');
  const [txCategory, setTxCategory] = useState('');

  // Use backend summary for balance
  const totalBalance = summary?.balance ? parseFloat(summary.balance) : 0;

  // Use backend summary for daily activity
  const dailySummary = {
    income: summary?.income_24h ? parseFloat(summary.income_24h) : 0,
    expense: summary?.expenses_24h ? parseFloat(summary.expenses_24h) : 0
  };

  // Filter transactions by Time Range first (used for Denominator in percentage calc)
  const transactionsInTimeRange = useMemo(() => {
    return transactions.filter(tx => {
      let matchesTime = true;
      const dateLower = tx.date.toLowerCase();

      if (timeRange === 'Jour') {
        matchesTime = dateLower.includes('aujourd') || dateLower.includes('today') || dateLower.includes('maintenant');
      } else if (timeRange === 'Semaine') {
        matchesTime = dateLower.includes('aujourd') || dateLower.includes('today') || dateLower.includes('hier') || dateLower.includes('yesterday') || dateLower.includes('maintenant');
      }
      // Implicitly 'Mois' and 'Année' return all in this mock logic as dates aren't fully parsed objects
      return matchesTime;
    });
  }, [transactions, timeRange]);

  // Calculate Totals for the selected Time Range
  const periodTotals = useMemo(() => {
    return {
      income: transactionsInTimeRange.filter(t => t.type === 'income').reduce((acc, t) => acc + t.amount, 0),
      expense: transactionsInTimeRange.filter(t => t.type === 'expense').reduce((acc, t) => acc + t.amount, 0)
    };
  }, [transactionsInTimeRange]);

  // Apply Search Filter on top of Time Range for display
  const filteredTransactions = useMemo(() => {
    return transactionsInTimeRange
      .filter(tx => tx.name.toLowerCase().includes(searchQuery.toLowerCase()))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [transactionsInTimeRange, searchQuery]);

  const handlePrintReport = () => {
    // Generate a print-friendly HTML string
    const printContent = `
      <html>
        <head>
          <title>Rapport Financier - Akompta AI</title>
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
            body { font-family: 'Poppins', sans-serif; padding: 40px; color: #1f2937; }
            .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #14532d; padding-bottom: 20px; }
            .header h1 { color: #14532d; margin: 0; font-size: 24px; }
            .header p { color: #6b7280; font-size: 14px; margin-top: 5px; }
            
            .summary { display: flex; gap: 20px; margin-bottom: 30px; }
            .card { flex: 1; background: #f9fafb; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; }
            .card-label { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
            .card-value { font-size: 20px; font-weight: 600; color: #14532d; margin-top: 5px; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background-color: #14532d; color: white; text-align: left; padding: 12px; font-size: 14px; font-weight: 500; }
            td { border-bottom: 1px solid #e5e7eb; padding: 12px; font-size: 14px; }
            tr:nth-child(even) { background-color: #f9fafb; }
            
            .income { color: #059669; font-weight: 600; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .expense { color: #dc2626; font-weight: 600; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .amount-inc { color: #059669; font-weight: 600; text-align: right; }
            .amount-exp { color: #dc2626; font-weight: 600; text-align: right; }
            
            .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 20px; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Rapport Financier</h1>
            <p>Généré le ${new Date().toLocaleDateString()} à ${new Date().toLocaleTimeString()}</p>
          </div>
          
          <div class="summary">
             <div class="card">
                <div class="card-label">Solde Actuel</div>
                <div class="card-value">${totalBalance.toLocaleString()} FCFA</div>
             </div>
             <div class="card">
                <div class="card-label">Transactions</div>
                <div class="card-value">${filteredTransactions.length}</div>
             </div>
          </div>

          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Libellé</th>
                <th>Type</th>
                <th style="text-align: right;">Montant</th>
              </tr>
            </thead>
            <tbody>
              ${filteredTransactions.map(tx => `
                <tr>
                  <td>${tx.date}</td>
                  <td>${tx.name}</td>
                  <td>
                    <span class="${tx.type === 'income' ? 'income' : 'expense'}">
                      ${tx.type === 'income' ? 'REVENU' : 'DÉPENSE'}
                    </span>
                  </td>
                  <td class="${tx.type === 'income' ? 'amount-inc' : 'amount-exp'}">
                    ${tx.type === 'income' ? '+' : '-'}${tx.amount} ${tx.currency}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <div class="footer">
            Document généré par Akompta AI - Votre assistant financier intelligent.
          </div>
        </body>
      </html>
    `;

    const printWindow = window.open('', '', 'height=600,width=800');
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 500);
    }
  };

  const handlePrintReceipt = (tx: Transaction) => {
    const printContent = `
      <html>
        <head>
          <title>Reçu #${tx.id} - Akompta AI</title>
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
            body { 
              font-family: 'Courier Prime', monospace; 
              padding: 40px; 
              background: #f3f3f3; 
              display: flex; 
              justify-content: center; 
            }
            .receipt {
              width: 300px;
              background: white;
              padding: 20px;
              box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .center { text-align: center; }
            .divider { border-bottom: 1px dashed #000; margin: 15px 0; }
            .row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
            .total { font-weight: bold; font-size: 16px; margin-top: 10px; }
            .footer { font-size: 10px; text-align: center; margin-top: 20px; color: #555; }
          </style>
        </head>
        <body>
          <div class="receipt">
             <div class="center">
               <h2 style="margin:0;">AKOMPTA AI</h2>
               <p style="font-size: 12px; margin: 5px 0;">Reçu de Transaction</p>
             </div>
             
             <div class="divider"></div>
             
             <div class="row">
               <span>DATE</span>
               <span>${tx.date}</span>
             </div>
             <div class="row">
               <span>ID</span>
               <span>#${tx.id}</span>
             </div>
             <div class="row">
               <span>TYPE</span>
               <span>${tx.type === 'income' ? 'REVENU' : 'DÉPENSE'}</span>
             </div>
             
             <div class="divider"></div>
             
             <div class="row" style="font-weight: bold;">
               <span>${tx.name.toUpperCase()}</span>
             </div>
             
             <div class="divider"></div>
             
             <div class="row total">
               <span>TOTAL</span>
               <span>${tx.amount} ${tx.currency}</span>
             </div>
             
             <div class="divider"></div>
             
             <div class="footer">
               Merci d'utiliser Akompta AI.<br/>
               Conservez ce reçu pour vos dossiers.
             </div>
          </div>
          <script>
            window.onload = function() { window.print(); window.close(); }
          </script>
        </body>
      </html>
    `;

    const printWindow = window.open('', '', 'height=600,width=400');
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
    }
  };

  const openModal = (type: 'income' | 'expense') => {
    setTxName('');
    setTxAmount('');
    setTxCategory(type === 'income' ? 'Vente' : 'Divers');
    setActiveModal(type);
  };

  const handleSaveTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txName || !txAmount || isSaving) return;

    setIsSaving(true);
    try {
      await onAddTransaction({
        name: txName,
        amount: parseFloat(txAmount),
        currency: 'FCFA',
        type: activeModal === 'income' ? 'income' : 'expense',
        date: new Date().toISOString(),
        percentage: 0,
        category: txCategory || (activeModal === 'income' ? 'Vente' : 'Divers')
      });

      // Refetch all related data
      await Promise.all([
        refetchSummary(),
        refetchAnalytics()
      ]);

      setTxName('');
      setTxAmount('');
      setTxCategory('');
      setActiveModal(null);
    } catch (error) {
      console.error("Error saving transaction:", error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-secondary dark:bg-gray-900 relative transition-colors">
      <Header
        title="Portefeuille"
        onBack={() => onNavigate(Screen.DASHBOARD)}
        onMenu={onToggleMenu}
        actionIcon={<Printer size={24} />}
        onAction={handlePrintReport}
      />

      <div className="flex-1 overflow-y-auto no-scrollbar pb-24">
        <div className="px-6">
          <div className="bg-[#6b9c88] dark:bg-gray-800 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden h-[380px] transition-colors">
            {/* Card Content */}
            <div className="flex items-start gap-4 mb-2">
              <div className="w-12 h-12 rounded-full bg-white dark:bg-gray-700 text-primary dark:text-green-400 flex items-center justify-center font-bold text-xl transition-colors">
                <Wallet size={24} />
              </div>
              <div>
                <div className="text-primary dark:text-green-300 opacity-80 text-lg">Solde Total</div>
                <div className="text-primary dark:text-white text-3xl font-bold">{totalBalance.toLocaleString()} FCFA</div>
                <div className="inline-block bg-[#4d7c6a] dark:bg-green-700 text-white text-xs px-2 py-0.5 rounded mt-1">Actif</div>
              </div>
            </div>

            <div className="flex justify-center mt-2 mb-4">
              <ChevronDown className="text-primary dark:text-green-400" />
            </div>

            {/* Chart Overlay */}
            <div className="h-40 w-full mb-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={balanceHistory.length > 0 ? balanceHistory.map(item => ({ name: item.date, value: parseFloat(item.balance) })) : [{ name: '', value: 0 }]}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14532d" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#14532d" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorValueDark" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34d399" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '12px',
                      backgroundColor: isDarkMode ? '#1f2937' : '#fff',
                      border: 'none',
                      fontSize: '12px',
                      color: isDarkMode ? '#fff' : '#000'
                    }}
                    itemStyle={{ color: isDarkMode ? '#34d399' : '#14532d' }}
                    labelStyle={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}
                  />
                  <Area type="monotone" dataKey="value" stroke={isDarkMode ? '#34d399' : '#14532d'} strokeWidth={3} fillOpacity={1} fill={`url(#${isDarkMode ? 'colorValueDark' : 'colorValue'})`} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="flex justify-between text-primary dark:text-green-300 text-xs font-medium">
              <span>{balanceHistory.length > 0 ? balanceHistory[0].date : 'Début'}</span>
              <span>{balanceHistory.length > 0 ? balanceHistory[balanceHistory.length - 1].date : 'Fin'}</span>
            </div>
          </div>

          {/* Interactive Time Filters */}
          <div className="flex justify-between px-2 mt-4 text-primary dark:text-green-400 font-medium">
            {['Jour', 'Semaine', 'Mois', 'Année'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range as any)}
                className={`px-4 py-1 rounded-lg text-sm transition-all ${timeRange === range
                  ? 'bg-white dark:bg-gray-800 shadow-sm font-bold opacity-100 scale-105'
                  : 'opacity-60 hover:opacity-100'
                  }`}
              >
                {range}
              </button>
            ))}
          </div>

          {/* Daily Summary Section */}
          <div className="grid grid-cols-2 gap-3 mt-4 mb-2">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm flex flex-col justify-between border-l-4 border-green-500 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider">Revenus (24h)</div>
                <div className="bg-green-100 dark:bg-green-900/30 p-1.5 rounded-full text-green-600 dark:text-green-400">
                  <ArrowUpRight size={14} />
                </div>
              </div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">+{dailySummary.income.toLocaleString()} F</div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm flex flex-col justify-between border-l-4 border-red-500 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider">Dépenses (24h)</div>
                <div className="bg-red-100 dark:bg-red-900/30 p-1.5 rounded-full text-red-500 dark:text-red-400">
                  <ArrowDownLeft size={14} />
                </div>
              </div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">-{dailySummary.expense.toLocaleString()} F</div>
            </div>
          </div>

          {/* Search Bar */}
          <div className="mt-4 mb-2">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-primary/50 dark:text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Rechercher une transaction..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white dark:bg-gray-800 rounded-full py-3 pl-12 pr-4 text-sm text-primary dark:text-white placeholder-primary/40 dark:placeholder-gray-500 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 dark:focus:ring-green-500/20 transition-colors"
              />
            </div>
          </div>

          <div className="mt-4 mb-4">
            <div className="flex justify-between items-center mb-3 px-2">
              <h3 className="text-primary dark:text-white font-bold">Transactions Récentes</h3>
              <button
                onClick={() => onNavigate(Screen.TRANSACTIONS)}
                className="text-sm text-primary/70 dark:text-green-400 font-medium hover:text-primary dark:hover:text-green-300 hover:underline"
              >
                Voir tout
              </button>
            </div>
            <div className="space-y-3">
              {filteredTransactions.length > 0 ? (
                filteredTransactions.map((tx) => {
                  const totalForType = tx.type === 'income' ? periodTotals.income : periodTotals.expense;
                  const percentage = totalForType > 0 ? ((tx.amount / totalForType) * 100).toFixed(1) : '0.0';

                  return (
                    <div
                      key={tx.id}
                      onClick={() => setSelectedTransaction(tx)}
                      className="bg-white dark:bg-gray-800 p-4 rounded-2xl flex justify-between items-center shadow-sm hover:shadow-md transition-all cursor-pointer active:scale-[0.98]"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 ${tx.type === 'income' ? 'bg-green-50 dark:bg-green-900/30 border-green-100 dark:border-green-800 text-green-600 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/30 border-red-100 dark:border-red-800 text-red-500 dark:text-red-400'}`}>
                          {tx.type === 'income' ? <ArrowUpRight size={20} /> : <ArrowDownLeft size={20} />}
                        </div>
                        <div>
                          <div className="font-bold text-gray-800 dark:text-white text-base">{tx.name}</div>
                          <div className="flex items-center gap-1.5 mt-1 text-gray-500 dark:text-gray-400">
                            <Calendar size={12} />
                            <span className="text-xs font-medium">{tx.date}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-bold text-lg ${tx.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
                          {tx.type === 'income' ? '+' : '-'}{tx.amount}
                        </div>
                        <div className="flex flex-col items-end mt-1">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${tx.type === 'income' ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'}`}>
                            {tx.type === 'income' ? 'Revenu' : 'Dépense'}
                          </span>
                          <span className="text-[10px] text-gray-400 dark:text-gray-500 mt-1 font-medium">{percentage}% du total</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8 text-primary/50 dark:text-gray-500 text-sm">
                  Aucune transaction trouvée.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Floating Action Buttons */}
      <div className="absolute bottom-24 right-6 flex items-center gap-4 z-20">
        <button
          onClick={() => openModal('expense')}
          className="w-14 h-14 bg-red-500 text-white rounded-full shadow-xl flex items-center justify-center hover:scale-105 active:scale-95 transition-transform hover:bg-red-600"
          title="Ajouter une dépense"
        >
          <Minus size={32} />
        </button>
        <button
          onClick={() => openModal('income')}
          className="w-14 h-14 bg-primary text-white rounded-full shadow-xl flex items-center justify-center hover:scale-105 active:scale-95 transition-transform hover:bg-primary/90"
          title="Ajouter un revenu"
        >
          <Plus size={32} />
        </button>
      </div>

      {/* Transaction Details Modal */}
      {selectedTransaction && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity" onClick={() => setSelectedTransaction(null)}></div>

          <div className="bg-white dark:bg-gray-800 w-full max-w-sm rounded-[30px] p-6 relative z-10 shadow-2xl animate-in zoom-in-95 duration-200">
            <button
              onClick={() => setSelectedTransaction(null)}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full text-gray-500 dark:text-gray-300 transition-colors"
            >
              <X size={18} />
            </button>

            <div className="flex flex-col items-center pt-2">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 border-white dark:border-gray-700 shadow-lg mb-4 ${selectedTransaction.type === 'income' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-500 dark:text-red-400'}`}>
                {selectedTransaction.type === 'income' ? <ArrowUpRight size={32} /> : <ArrowDownLeft size={32} />}
              </div>

              <div className="text-sm text-gray-500 dark:text-gray-400 uppercase tracking-widest font-bold mb-1">
                {selectedTransaction.type === 'income' ? 'Revenu' : 'Dépense'}
              </div>
              <div className={`text-3xl font-bold mb-6 ${selectedTransaction.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
                {selectedTransaction.type === 'income' ? '+' : '-'}{selectedTransaction.amount} {selectedTransaction.currency}
              </div>

              <div className="w-full bg-gray-50 dark:bg-gray-700 rounded-2xl p-4 space-y-4 mb-6 transition-colors">
                <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-600 pb-3">
                  <span className="text-gray-500 dark:text-gray-400 text-sm">Libellé</span>
                  <span className="font-bold text-gray-800 dark:text-white">{selectedTransaction.name}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-600 pb-3">
                  <span className="text-gray-500 dark:text-gray-400 text-sm">Date</span>
                  <span className="font-bold text-gray-800 dark:text-white">{selectedTransaction.date}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-600 pb-3">
                  <span className="text-gray-500 dark:text-gray-400 text-sm">Catégorie</span>
                  <span className="font-bold text-gray-800 dark:text-white">
                    {selectedTransaction.category || (selectedTransaction.type === 'income' ? 'Ventes' : 'Achats')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 dark:text-gray-400 text-sm">ID Transaction</span>
                  <span className="font-mono text-xs bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded text-gray-600 dark:text-gray-300">#{selectedTransaction.id}</span>
                </div>
              </div>

              <div className="flex gap-3 w-full">
                <button className="flex-1 py-3 rounded-2xl bg-primary/10 dark:bg-white/10 text-primary dark:text-white font-bold text-sm hover:bg-primary/20 dark:hover:bg-white/20 transition-colors flex items-center justify-center gap-2">
                  <Share2 size={16} /> Partager
                </button>
                <button
                  onClick={() => handlePrintReceipt(selectedTransaction)}
                  className="flex-1 py-3 rounded-2xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/30 hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                >
                  <FileText size={16} /> Reçu
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unified Add Modal */}
      {activeModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity" onClick={() => setActiveModal(null)}></div>

          {/* Modal Content */}
          <div className="bg-white dark:bg-gray-800 w-full max-w-sm rounded-[30px] p-6 relative z-10 shadow-2xl animate-in zoom-in-95 duration-200">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-6 text-center">
              {activeModal === 'income' ? 'Ajouter un revenu' : 'Ajouter une dépense'}
            </h3>

            <form onSubmit={handleSaveTransaction} className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Description</label>
                <input
                  value={txName}
                  onChange={(e) => setTxName(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white"
                  placeholder={activeModal === 'income' ? "Ex: Vente de Mais" : "Ex: Paiement facture"}
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Montant (FCFA)</label>
                <input
                  type="number"
                  value={txAmount}
                  onChange={(e) => setTxAmount(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-bold text-lg"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Catégorie</label>
                <select
                  value={txCategory}
                  onChange={(e) => setTxCategory(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                >
                  {activeModal === 'income' ? (
                    <>
                      <option value="Vente">Vente</option>
                      <option value="Service">Service</option>
                      <option value="Autre">Autre</option>
                    </>
                  ) : (
                    <>
                      <option value="Divers">Divers</option>
                      <option value="Stock">Stock</option>
                      <option value="Transport">Transport</option>
                      <option value="Loyer">Loyer</option>
                      <option value="Electricité">Electricité</option>
                      <option value="Eau">Eau</option>
                      <option value="Equipement">Equipement</option>
                      <option value="Salaires">Salaires</option>
                    </>
                  )}
                </select>
              </div>

              <div className="flex gap-3 w-full mt-8">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="flex-1 py-3.5 rounded-2xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-bold text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className={`flex-1 py-3.5 rounded-2xl text-white font-bold text-sm shadow-lg transition-colors flex items-center justify-center gap-2 ${activeModal === 'income' ? 'bg-primary shadow-primary/30 hover:bg-primary/90' : 'bg-red-500 shadow-red-500/30 hover:bg-red-600'} disabled:opacity-50`}
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

export default WalletScreen;

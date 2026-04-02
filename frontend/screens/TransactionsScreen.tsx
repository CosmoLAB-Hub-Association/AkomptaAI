
import React, { useState, useMemo } from 'react';
import { Screen, Transaction } from '../types';
import { Header } from '../components/Shared';
import { Search, ArrowUpRight, ArrowDownLeft, Calendar, Filter, ArrowUpDown, Share2, FileText, X } from 'lucide-react';

interface Props {
  onNavigate: (screen: Screen) => void;
  transactions: Transaction[];
  onToggleMenu: () => void;
}

const TransactionsScreen: React.FC<Props> = ({ onNavigate, transactions, onToggleMenu }) => {
  const [filterType, setFilterType] = useState<'all' | 'income' | 'expense'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  const filteredTransactions = useMemo(() => {
    let result = transactions;

    // Filter by type
    if (filterType !== 'all') {
      result = result.filter(t => t.type === filterType);
    }

    // Filter by search
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(t => 
        t.name.toLowerCase().includes(q) || 
        (t.category && t.category.toLowerCase().includes(q)) ||
        t.amount.toString().includes(q)
      );
    }
    
    // Sort logic
    const sorted = [...result].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return sorted;
  }, [transactions, filterType, searchQuery, sortOrder]);

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

  return (
    <div className="flex flex-col h-full bg-secondary dark:bg-gray-900 pb-24 overflow-y-auto no-scrollbar transition-colors">
      <Header 
        title="Historique" 
        onBack={() => onNavigate(Screen.WALLET)} 
        onMenu={onToggleMenu} 
      />
      
      <div className="px-6 flex flex-col gap-4">
        {/* Search & Sort Row */}
        <div className="flex gap-2">
            <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                <input 
                    type="text" 
                    placeholder="Rechercher..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-white dark:bg-gray-800 rounded-2xl py-3 pl-12 pr-4 text-sm text-gray-800 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20 dark:focus:ring-green-500/20 shadow-sm transition-colors"
                />
            </div>
            <button 
                onClick={() => setSortOrder(prev => prev === 'newest' ? 'oldest' : 'newest')}
                className="w-12 bg-white dark:bg-gray-800 rounded-2xl flex items-center justify-center text-primary dark:text-green-400 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                title={sortOrder === 'newest' ? 'Plus récents' : 'Plus anciens'}
            >
                <ArrowUpDown size={20} />
            </button>
        </div>

        {/* Filter Chips */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
            {[
                { id: 'all', label: 'Tout' },
                { id: 'income', label: 'Revenus' },
                { id: 'expense', label: 'Dépenses' }
            ].map(type => (
                <button
                    key={type.id}
                    onClick={() => setFilterType(type.id as any)}
                    className={`px-5 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                        filterType === type.id 
                        ? 'bg-primary text-white shadow-lg shadow-primary/20' 
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                >
                    {type.label}
                </button>
            ))}
        </div>

        {/* List */}
        <div className="space-y-3 mt-2">
            {filteredTransactions.length > 0 ? (
                filteredTransactions.map(tx => (
                    <div 
                        key={tx.id}
                        onClick={() => setSelectedTransaction(tx)}
                        className="bg-white dark:bg-gray-800 p-4 rounded-2xl flex justify-between items-center shadow-sm hover:shadow-md transition-all active:scale-[0.99] cursor-pointer border border-transparent hover:border-primary/5"
                    >
                        <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 ${
                                tx.type === 'income' 
                                ? 'bg-green-50 dark:bg-green-900/30 border-green-100 dark:border-green-800 text-green-600 dark:text-green-400' 
                                : 'bg-red-50 dark:bg-red-900/30 border-red-100 dark:border-red-800 text-red-500 dark:text-red-400'
                            }`}>
                                {tx.type === 'income' ? <ArrowUpRight size={20} /> : <ArrowDownLeft size={20} />}
                            </div>
                            <div>
                                <div className="font-bold text-gray-800 dark:text-white text-base">{tx.name}</div>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-wide ${
                                        tx.type === 'income' ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
                                    }`}>
                                        {tx.category || (tx.type === 'income' ? 'Vente' : 'Dépense')}
                                    </span>
                                    <span className="text-xs text-gray-400 flex items-center gap-1">
                                        <Calendar size={10} /> {tx.date}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="text-right">
                             <div className={`font-bold text-lg ${tx.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
                                {tx.type === 'income' ? '+' : '-'}{tx.amount}
                            </div>
                             <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                {tx.currency}
                            </div>
                        </div>
                    </div>
                ))
            ) : (
                <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                        <Filter size={24} />
                    </div>
                    <p>Aucune transaction trouvée.</p>
                </div>
            )}
        </div>
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
    </div>
  );
};

export default TransactionsScreen;

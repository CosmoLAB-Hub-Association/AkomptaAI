import React, { useState, useEffect, useMemo } from 'react';
import { Screen, Product, Transaction } from '../types';
import { Header } from '../components/Shared';
import { Search, Heart, Mic, ShoppingBag, Plus, X, Edit, Trash2, AlertTriangle, Download, Save, Loader2 } from 'lucide-react';
import { useProducts, useTransactions } from '../hooks';

interface Props {
  onNavigate: (screen: Screen) => void;
  onToggleMenu: () => void;
}

const ProductCard: React.FC<{
  product: Product;
  onClick: () => void;
  isEditing: boolean;
  onEditStart: (e: React.MouseEvent) => void;
  onSave: (p: Product) => void;
  onCancel: () => void;
}> = ({ product, onClick, isEditing, onEditStart, onSave, onCancel }) => {
  const [formData, setFormData] = useState<Product>(product);

  useEffect(() => {
    setFormData(product);
  }, [product, isEditing]);

  const handleChange = (field: keyof Product, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (isEditing) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-[30px] p-4 mb-4 shadow-lg border-2 border-primary dark:border-green-600 relative cursor-default transition-colors" onClick={(e) => e.stopPropagation()}>
        <div className="flex gap-4">
          <div className="w-20 h-20 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-700 shrink-0 border-2 border-gray-200 dark:border-gray-600">
            <img src={formData.image} alt="Product" className="w-full h-full object-cover opacity-70" />
          </div>
          <div className="flex-1 space-y-2">
            <input
              value={formData.name}
              onChange={e => handleChange('name', e.target.value)}
              className="w-full text-lg font-bold text-primary dark:text-green-400 border-b border-gray-200 dark:border-gray-600 outline-none p-0 bg-transparent placeholder-gray-400"
              placeholder="Nom du produit"
              autoFocus
            />
            <textarea
              value={formData.description}
              onChange={e => handleChange('description', e.target.value)}
              className="w-full text-xs text-gray-600 dark:text-gray-300 border border-gray-100 dark:border-gray-600 rounded-lg p-2 outline-none resize-none bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:ring-2 focus:ring-primary/10 transition-all"
              rows={2}
              placeholder="Description courte"
            />
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  value={formData.price}
                  onChange={e => handleChange('price', e.target.value)}
                  className="w-full text-sm font-bold border-b border-gray-200 dark:border-gray-600 outline-none pb-1 bg-transparent dark:text-white"
                  placeholder="Prix"
                  type="number"
                />
                <span className="absolute right-0 bottom-1 text-xs text-gray-400">F</span>
              </div>
              <div className="w-20">
                <input
                  value={formData.unit}
                  onChange={e => handleChange('unit', e.target.value)}
                  className="w-full text-sm border-b border-gray-200 dark:border-gray-600 outline-none pb-1 text-center bg-transparent dark:text-white"
                  placeholder="Unité"
                />
              </div>
            </div>
            <select
              value={formData.stockStatus || 'ok'}
              onChange={e => handleChange('stockStatus', e.target.value)}
              className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-100 dark:border-gray-600 rounded-lg p-1.5 outline-none text-gray-700 dark:text-gray-200"
            >
              <option value="ok">En Stock</option>
              <option value="low">Faible</option>
              <option value="rupture">Rupture</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-2 border-t border-gray-100 dark:border-gray-700">
          <button onClick={onCancel} className="px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 font-medium text-xs hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            Annuler
          </button>
          <button onClick={() => onSave(formData)} className="px-4 py-2 rounded-full bg-primary text-white font-medium text-xs shadow-lg shadow-primary/20 hover:bg-primary/90 transition-colors flex items-center gap-1">
            <Save size={14} /> Enregistrer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div onClick={onClick} className="bg-white dark:bg-gray-800 rounded-[30px] p-4 flex gap-4 mb-4 shadow-sm relative overflow-hidden active:scale-[0.99] transition-all cursor-pointer group hover:shadow-md border border-transparent hover:border-primary/10 dark:hover:border-green-400/20">
      <div className="w-24 h-24 rounded-full overflow-hidden flex-shrink-0 border-2 border-gray-100 dark:border-gray-700">
        <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
      </div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex justify-between items-start">
          <h3 className="text-primary dark:text-green-400 text-lg font-bold">{product.name}</h3>
          <div className="flex gap-1 text-primary dark:text-green-400">
            <button
              onClick={onEditStart}
              className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-primary/10 dark:hover:bg-white/10 text-primary/70 dark:text-green-400/70 hover:text-primary dark:hover:text-green-400 transition-all"
              title="Modifier"
            >
              <Edit size={16} />
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 my-1">{product.description}</p>
        <div className="flex justify-between items-center mt-1">
          <div className="flex gap-1">
            <span className="bg-primary/10 dark:bg-green-900/40 text-primary dark:text-green-300 text-[10px] px-2 py-0.5 rounded-full">Medium</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full ${product.stockStatus === 'rupture' ? 'bg-orange-500 text-white' : 'bg-primary dark:bg-green-600 text-white'}`}>
              {product.stockStatus === 'rupture' ? 'rupture' : 'Stock'}
            </span>
          </div>
          <div className="bg-primary dark:bg-green-600 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1 font-medium shadow-sm">
            {product.price}F/{product.unit}
            <ShoppingBag size={10} />
          </div>
        </div>
      </div>
    </div>
  );
};

const TransactionItem: React.FC<{ transaction: Transaction }> = ({ transaction }) => {
  const isIncome = transaction.type === 'income';
  return (
    <div className="bg-white dark:bg-gray-800 rounded-[30px] p-4 flex gap-4 mb-4 shadow-sm border-l-4 border-l-primary dark:border-l-green-500">
      <div className={`w-14 h-14 rounded-full flex items-center justify-center shrink-0 ${isIncome ? 'bg-green-100 dark:bg-green-900/30 text-green-600' : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600'}`}>
        <ShoppingBag size={24} />
      </div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex justify-between items-center">
          <h3 className="text-primary dark:text-white text-md font-bold">{transaction.name}</h3>
          <span className={`text-sm font-bold ${isIncome ? 'text-green-600' : 'text-orange-500'}`}>
            {isIncome ? '+' : '-'}{transaction.amount} F
          </span>
        </div>
        <div className="flex justify-between items-center mt-1">
          <span className="text-[10px] text-gray-400 uppercase tracking-tighter">{transaction.category}</span>
          <span className="text-[10px] text-gray-400">{new Date(transaction.date).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
};

const ManagementScreen: React.FC<Props> = ({ onNavigate, onToggleMenu }) => {
  const { data: products, loading: productsLoading, addProduct, updateProduct, deleteProduct } = useProducts();
  const { data: transactions, loading: txLoading } = useTransactions();
  const [activeTab, setActiveTab] = useState<'Vente' | 'Dépenses' | 'Produits' | 'Stock'>('Vente');
  const [showPromo, setShowPromo] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Edit Mode States
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editFormData, setEditFormData] = useState<Product | null>(null);

  // Mixed items (Products + Transactions) based on the active tab
  const sortedItems = useMemo(() => {
    let items: any[] = [];
    
    if (activeTab === 'Produits') {
      items = products;
    } else if (activeTab === 'Stock') {
      items = products.filter(p => p.category?.toLowerCase() === 'stock' || p.stockStatus === 'low' || p.stockStatus === 'rupture');
    } else {
      const catProducts = products.filter(product => {
        const category = product.category?.toLowerCase() || '';
        if (activeTab === 'Dépenses') return category === 'depense' || category === 'dépense';
        if (activeTab === 'Vente') return category === 'vente';
        return false;
      });

      const catTransactions = transactions.filter(tx => {
        if (activeTab === 'Vente') return tx.type === 'income';
        if (activeTab === 'Dépenses') return tx.type === 'expense';
        return false;
      });
      items = [...catProducts, ...catTransactions];
    }

    return [...items].sort((a: any, b: any) => {
      const dateA = new Date(a.date || a.created_at || 0).getTime();
      const dateB = new Date(b.date || b.created_at || 0).getTime();
      return dateB - dateA;
    });
  }, [activeTab, products, transactions]);

  const filteredItems = sortedItems;

  const handleDeleteProduct = async () => {
    if (selectedProduct && selectedProduct.id) {
      await deleteProduct(selectedProduct.id);
      setSelectedProduct(null);
      setShowDeleteConfirm(false);
    }
  };

  const closeProductModal = () => {
    setSelectedProduct(null);
    setShowDeleteConfirm(false);
    setIsEditing(false);
    setIsCreating(false);
    setEditFormData(null);
  };

  // Create Product Handler
  const handleStartAddProduct = () => {
    const newProduct: Product = {
      id: '', // Will be generated on save
      name: '',
      description: '',
      price: '',
      unit: 'Kg',
      image: `https://picsum.photos/seed/${Date.now()}/200/200`,
      category: 'Vente',
      stockStatus: 'ok'
    };
    setSelectedProduct(newProduct);
    setEditFormData(newProduct);
    setIsEditing(true);
    setIsCreating(true);
  };

  // Modal Edit Handlers
  const handleEditClick = () => {
    if (selectedProduct) {
      setEditFormData({ ...selectedProduct });
      setIsEditing(true);
    }
  };

  const handleSaveEdit = async () => {
    if (editFormData && !isSaving) {
      setIsSaving(true);
      try {
        if (isCreating) {
          // Create new product
          await addProduct({
            name: editFormData.name,
            description: editFormData.description,
            price: editFormData.price,
            unit: editFormData.unit,
            category: editFormData.category.toLowerCase().replace('é', 'e'),
            stock_status: editFormData.stockStatus || 'ok'
          });
          setIsCreating(false);
        } else {
          // Update existing product
          if (editFormData.id) {
            await updateProduct(editFormData.id, {
              name: editFormData.name,
              description: editFormData.description,
              price: editFormData.price,
              unit: editFormData.unit,
              category: editFormData.category.toLowerCase().replace('é', 'e'),
              stock_status: editFormData.stockStatus || 'ok'
            });
          }
        }

        setSelectedProduct(null);
        setIsEditing(false);
        setEditFormData(null);
      } catch (error) {
        console.error("Error saving product:", error);
      } finally {
        setIsSaving(false);
      }
    }
  };

  const handleCancelEdit = () => {
    if (isCreating) {
      closeProductModal();
    } else {
      setIsEditing(false);
      setEditFormData(null);
    }
  };

  // Inline Edit Handlers
  const handleInlineSave = async (updatedProduct: Product) => {
    if (updatedProduct.id) {
      await updateProduct(updatedProduct.id, {
        name: updatedProduct.name,
        description: updatedProduct.description,
        price: updatedProduct.price,
        unit: updatedProduct.unit,
        category: updatedProduct.category.toLowerCase().replace('é', 'e'),
        stock_status: updatedProduct.stockStatus || 'ok'
      });
    }
    setEditingId(null);
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Nom', 'Description', 'Prix', 'Unité', 'Catégorie', 'Statut'];
    const rows = products.map(p => [
      p.id,
      `"${p.name.replace(/"/g, '""')}"`, // Escape quotes
      `"${p.description.replace(/"/g, '""')}"`,
      p.price,
      p.unit,
      p.category,
      p.stockStatus || 'ok'
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'akompta_export.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col h-full bg-secondary dark:bg-gray-900 pb-24 relative transition-colors">
      <Header
        title="Gestion"
        onBack={() => onNavigate(Screen.DASHBOARD)}
        onMenu={onToggleMenu}
        actionIcon={<Download size={24} />}
        onAction={handleExportCSV}
      />

      <div className="px-6 pb-2">
        <div className="flex justify-between items-center mb-4">
          <div className="bg-transparent border border-orange-400/50 rounded-full px-4 py-2 flex items-center flex-1 mr-4">
            <Search size={18} className="text-primary dark:text-green-400 mr-2" />
            <input placeholder="Search" className="bg-transparent outline-none text-sm w-full text-primary dark:text-white placeholder-primary dark:placeholder-gray-500" />
          </div>
          <div className="text-primary dark:text-white text-sm font-medium">Page de gestion</div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar mb-6">
          {['Vente', 'Dépenses', 'Produits', 'Stock'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors ${activeTab === tab ? 'bg-primary text-white' : 'bg-primary/80 dark:bg-gray-700 text-white/90 dark:text-gray-300'
                }`}
            >
              {tab}
            </button>
          ))}
          <button
            onClick={handleStartAddProduct}
            className="bg-primary text-white p-1.5 rounded-full shadow-lg shadow-primary/20 active:scale-95 transition-transform"
            title="Ajouter un produit"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      <div className="px-6 overflow-y-auto flex-1 no-scrollbar">
        {(productsLoading || txLoading) ? (
          <div className="flex justify-center py-10"><div className="w-8 h-8 border-4 border-primary border-t-transparent animate-spin rounded-full"></div></div>
        ) : filteredItems.length > 0 ? (
          filteredItems.map((item: any) => {
            const isProduct = 'price' in item && 'category' in item && !('amount' in item);
            if (isProduct) {
              return (
                <ProductCard
                  key={`prod-${item.id}`}
                  product={item}
                  onClick={() => setSelectedProduct(item)}
                  isEditing={editingId === item.id}
                  onEditStart={(e) => {
                    e.stopPropagation();
                    setEditingId(item.id);
                  }}
                  onSave={handleInlineSave}
                  onCancel={() => setEditingId(null)}
                />
              );
            } else {
              return <TransactionItem key={`tx-${item.id}`} transaction={item} />;
            }
          })
        ) : (
          <div className="flex flex-col items-center justify-center h-40 text-primary/50 dark:text-gray-500">
            <p>Aucun élément trouvé.</p>
          </div>
        )}
      </div>

      {showPromo && (
        <div className="absolute bottom-24 left-6 right-6 bg-primary dark:bg-green-700 text-white rounded-2xl p-4 flex items-center justify-between shadow-xl z-10 animate-in slide-in-from-bottom-4 duration-500">
          <div className="bg-white/10 p-2 rounded-xl mr-3">
            <div className="text-2xl font-bold">%</div>
          </div>
          <div className="flex-1">
            <div className="font-bold text-sm">Promo Special Free</div>
            <div className="text-xs opacity-80">Delivery for You !</div>
          </div>
          <div className="flex flex-col items-end">
            <div className="text-xs mb-1">Akompta AI</div>
            <div className="font-bold flex items-center gap-1">
              Premium
              <button className="bg-white/20 p-1 rounded-full text-white ml-2 hover:bg-white/30 transition-colors">Détails</button>
            </div>
          </div>
          <button onClick={() => setShowPromo(false)} className="absolute -top-2 -right-2 bg-white/90 hover:bg-white rounded-full p-1 text-primary shadow-sm">
            <X size={12} />
          </button>
        </div>
      )}

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity" onClick={closeProductModal}></div>

          {/* Modal Content */}
          <div className="bg-white dark:bg-gray-800 w-full max-w-sm rounded-[40px] p-6 relative z-10 shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto no-scrollbar">
            <button
              onClick={closeProductModal}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full text-gray-500 dark:text-gray-300 transition-colors z-20"
            >
              <X size={18} />
            </button>

            {showDeleteConfirm ? (
              <div className="flex flex-col items-center py-8 text-center">
                <div className="w-20 h-20 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center text-red-500 mb-4 animate-bounce">
                  <AlertTriangle size={36} />
                </div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-2">Supprimer le produit ?</h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-8 px-4">
                  Êtes-vous sûr de vouloir supprimer définitivement <span className="font-bold text-gray-700 dark:text-white">{selectedProduct.name}</span> ? Cette action est irréversible.
                </p>

                <div className="flex gap-3 w-full">
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="flex-1 py-3.5 rounded-2xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-white font-bold text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleDeleteProduct}
                    className="flex-1 py-3.5 rounded-2xl bg-red-500 text-white font-bold text-sm shadow-lg shadow-red-500/30 hover:bg-red-600 transition-colors"
                  >
                    Supprimer
                  </button>
                </div>
              </div>
            ) : isEditing && editFormData ? (
              <div className="flex flex-col pt-2">
                <h2 className="text-xl font-bold text-primary dark:text-white mb-6 text-center">
                  {isCreating ? 'Ajouter un produit' : 'Modifier le produit'}
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Nom</label>
                    <input
                      value={editFormData.name}
                      onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                      className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                      placeholder="Ex: Tomates"
                    />
                  </div>

                  <div className="flex gap-2">
                    <div className="flex-1">
                      <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Prix</label>
                      <input
                        type="number"
                        value={editFormData.price}
                        onChange={(e) => setEditFormData({ ...editFormData, price: e.target.value })}
                        className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                        placeholder="0"
                      />
                    </div>
                    <div className="w-1/3">
                      <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Unité</label>
                      <input
                        value={editFormData.unit}
                        onChange={(e) => setEditFormData({ ...editFormData, unit: e.target.value })}
                        className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                        placeholder="Kg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Catégorie</label>
                    <select
                      value={editFormData.category}
                      onChange={(e) => setEditFormData({ ...editFormData, category: e.target.value as any })}
                      className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                    >
                      <option value="Vente">Vente</option>
                      <option value="Dépense">Dépense</option>
                      <option value="Stock">Stock</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Statut Stock</label>
                    <select
                      value={editFormData.stockStatus || 'ok'}
                      onChange={(e) => setEditFormData({ ...editFormData, stockStatus: e.target.value as any })}
                      className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium"
                    >
                      <option value="ok">En Stock</option>
                      <option value="low">Faible</option>
                      <option value="rupture">Rupture</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase ml-2">Description</label>
                    <textarea
                      rows={3}
                      value={editFormData.description}
                      onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                      className="w-full bg-gray-50 dark:bg-gray-700 px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 text-gray-800 dark:text-white font-medium resize-none"
                      placeholder="Brève description..."
                    />
                  </div>
                </div>

                <div className="flex gap-3 w-full mt-8">
                  <button
                    onClick={handleCancelEdit}
                    className="flex-1 py-3.5 rounded-2xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-bold text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    disabled={isSaving}
                    className="flex-1 py-3.5 rounded-2xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/30 hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />} 
                    {isCreating ? (isSaving ? 'Création...' : 'Créer') : (isSaving ? 'Enregistrement...' : 'Enregistrer')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center pt-2">
                <div className="w-28 h-28 rounded-full overflow-hidden border-4 border-white dark:border-gray-700 shadow-lg mb-4">
                  <img src={selectedProduct.image} alt={selectedProduct.name} className="w-full h-full object-cover" />
                </div>

                <h2 className="text-2xl font-bold text-primary dark:text-white mb-1">{selectedProduct.name}</h2>
                <span className="text-gray-400 text-xs uppercase tracking-widest mb-3">{selectedProduct.category}</span>

                <div className={`text-xs px-3 py-1 rounded-full mb-6 font-medium ${selectedProduct.stockStatus === 'rupture' ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                  }`}>
                  {selectedProduct.stockStatus === 'rupture' ? 'Rupture de stock' : 'En Stock'}
                </div>

                <p className="text-center text-gray-500 dark:text-gray-400 text-sm mb-8 px-2 leading-relaxed">
                  {selectedProduct.description}
                </p>

                <div className="w-full bg-[#f0fdf4] dark:bg-green-900/10 border border-[#dcfce7] dark:border-green-800/50 rounded-2xl p-4 mb-8 flex justify-between items-center transition-colors">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Prix unitaire</div>
                    <div className="text-2xl font-bold text-primary dark:text-green-400">{selectedProduct.price} F <span className="text-sm font-normal text-gray-500 dark:text-gray-400">/ {selectedProduct.unit}</span></div>
                  </div>
                  <div className="bg-primary p-3 rounded-full shadow-lg shadow-primary/20 text-white">
                    <ShoppingBag size={20} />
                  </div>
                </div>

                <div className="flex gap-3 w-full">
                  <button
                    onClick={handleEditClick}
                    className="flex-1 py-3.5 rounded-2xl bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-bold text-sm hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors flex items-center justify-center gap-2">
                    <Edit size={16} /> Modifier
                  </button>
                  {selectedProduct.category === 'Vente' ? (
                    <button className="flex-1 py-3.5 rounded-2xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/30 hover:bg-primary/90 transition-colors">
                      Vendre
                    </button>
                  ) : (
                    <button
                      onClick={() => setShowDeleteConfirm(true)}
                      className="flex-1 py-3.5 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 font-bold text-sm hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors flex items-center justify-center gap-2"
                    >
                      <Trash2 size={16} /> Supprimer
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagementScreen;
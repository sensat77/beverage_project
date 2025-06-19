// pages/input/input.js (最终精确修正版 - 提成计算修复)
import { requestWithAuth } from '../../utils/api.js';

// 辅助函数：格式化日期为YYYY-MM-DD
const formatDate = date => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}

Page({
  data: {
    rawText: '',
    parsedData: null, // 智能解析后的数据
    isLoading: false, // 页面整体加载状态
    
    // 手动添加产品模态框相关数据
    showAddModal: false,
    searchKeyword: '',
    allProducts: [], // 所有产品列表，从后端获取
    searchResult: [],
    selectedProduct: null,
    newItemQuantity: '',
    newItemPrice: '',
    focusedInput: '', // 用于控制输入框聚焦样式

    selectedDate: formatDate(new Date()) // 默认选中今天
  },

  onLoad: function() {
    this.fetchAllProducts(); // 页面加载时获取所有产品列表
  },

  onShow: function() {
    if (this.data.parsedData) {
      this.recalculateTotals();
    }
  },

  // 获取所有产品列表
  async fetchAllProducts() {
      // 【新增】设置加载状态
    wx.showLoading({
        title: '加载产品中...',
        mask: true
      });
    try {
      const res = await requestWithAuth({ url: '/api/products/' });
      // 后端返回的 unit_price 和 commission_per_item 是字符串，需要转换为数字
      const products = res.map(p => ({
        ...p,
        unit_price: parseFloat(p.unit_price),
        commission_per_item: parseFloat(p.commission_per_item)
      }));
      this.setData({ allProducts: products || [] });
      wx.hideLoading(); // 【新增】隐藏加载提示
    } catch (error) {
      console.error("获取所有产品列表失败", error);
      wx.showToast({ title: '获取产品列表失败', icon: 'none' });
      wx.hideLoading(); // 【新增】隐藏加载提示
    }
  },

  onTextareaInput: function(e) {
    this.setData({ rawText: e.detail.value });
  },

  onDateChange: function(e) {
    this.setData({ selectedDate: e.detail.value });
  },

  async onParseTap() {
    if (!this.data.rawText.trim()) {
      wx.showToast({ title: '请输入订单内容', icon: 'none' });
      return;
    }
    this.setData({ isLoading: true });
    try {
      const result = await requestWithAuth({
        url: '/api/parse_order',
        method: 'POST',
        data: this.data.rawText,
        contentType: 'text/plain'
      });
      console.log('解析成功', result);
      
      if (result) {
        result.order_date = this.data.selectedDate;
        // 确保数值字段是数字类型，并进行初步格式化以避免NaN
        result.display_fee = parseFloat(result.display_fee || 0);
        result.old_goods_disposal_fee = parseFloat(result.old_goods_disposal_fee || 0);
        result.other_expenses = parseFloat(result.other_expenses || 0);
        result.total_gifting_cost = parseFloat(result.total_gifting_cost || 0);
        // 后端解析的总提成，作为参考值，前端会重新计算并显示
        result.total_commission = parseFloat(result.total_commission || 0); 
        
        result.total_item_count = parseInt(result.total_item_count || 0);

        if (result.order_items && result.order_items.length > 0) {
          result.order_items.forEach(item => {
            item.quantity = parseInt(item.quantity || 0);
            item.actual_unit_price = parseFloat(item.actual_unit_price || 0);
            item.item_amount = parseFloat(item.item_amount || 0);
            item.item_gifting_cost = parseFloat(item.item_gifting_cost || 0);

            // 【关键修正点】在解析时，根据 product_name 和 quantity 补齐 item_commission
            const productInfo = this.data.allProducts.find(p => p.name === item.product_name);
            item.item_commission = productInfo ? (parseFloat(productInfo.commission_per_item) * item.quantity) : 0;

            item.actual_unit_price_str = item.actual_unit_price.toFixed(2);
            item.item_gifting_cost_str = item.item_gifting_cost.toFixed(2);
          });
        }
        // 格式化需要显示的后端总计字段
        result.total_gifting_cost_str = result.total_gifting_cost.toFixed(2);
        // result.total_commission_str 稍后在 recalculateTotals 中设置
        
      }
      this.setData({ parsedData: result });
      this.recalculateTotals(); // 初始解析后也计算一次总计 (确保提成也计算)
    } catch (error) {
      wx.showToast({ title: error.message || '解析失败，请检查文本格式', icon: 'none' });
      console.error('解析失败', error);
      this.setData({ parsedData: null }); // 解析失败则清空数据
    } finally {
      this.setData({ isLoading: false });
    }
  },

  onFieldChange(e) {
    const { path, type, index } = e.currentTarget.dataset;
    let value = e.detail.value;

    if (type === 'number') {
        value = parseFloat(value) || 0;
        if (value < 0) value = 0;
    } else if (type === 'integer') {
        value = parseInt(value) || 0;
        if (value < 0) value = 0;
    }
    
    this.setData({ [path]: value });

    if (path.startsWith('parsedData.order_items')) {
        const productIndex = index;
        const currentItem = this.data.parsedData.order_items[productIndex];
        
        const updatedItem = { ...currentItem };

        const originalProduct = this.data.allProducts.find(p => p.name === updatedItem.product_name);
        const originalUnitPrice = originalProduct ? originalProduct.unit_price : 0;
        const commissionPerItem = originalProduct ? originalProduct.commission_per_item : 0;

        const updatedQuantity = (type === 'integer' && path.endsWith('.quantity')) ? value : updatedItem.quantity;
        const updatedActualPrice = (type === 'number' && path.endsWith('.actual_unit_price')) ? value : updatedItem.actual_unit_price;

        updatedItem.item_amount = updatedActualPrice * updatedQuantity;
        updatedItem.item_gifting_cost = Math.max(0, originalUnitPrice - updatedActualPrice) * updatedQuantity;
        updatedItem.item_commission = commissionPerItem * updatedQuantity; // 确保单项提成更新
        
        updatedItem.actual_unit_price_str = updatedActualPrice.toFixed(2);
        updatedItem.item_gifting_cost_str = updatedItem.item_gifting_cost.toFixed(2);
        
        this.setData({
            [`parsedData.order_items[${productIndex}]`]: updatedItem
        });
    }

    setTimeout(() => {
      this.recalculateTotals();
    }, 50);
  },

  onDeleteItem: function(e) {
    const index = e.currentTarget.dataset.index;
    let currentItems = this.data.parsedData.order_items;
    currentItems.splice(index, 1);
    this.setData({ 'parsedData.order_items': currentItems });
    this.recalculateTotals();
  },

  recalculateTotals: function() {
    if (!this.data.parsedData) return;
    const items = this.data.parsedData.order_items || [];
    let totalItems = 0;
    let totalOrderAmount = 0;
    let recalculatedTotalGiftingCost = 0;
    let recalculatedTotalCommission = 0; // 重新计算的总提成

    items.forEach(item => {
        totalItems += Number(item.quantity);
        totalOrderAmount += Number(item.quantity) * Number(item.actual_unit_price);
        recalculatedTotalGiftingCost += Number(item.item_gifting_cost);
        // 【关键修正】这里直接累加每个 item 的 item_commission
        recalculatedTotalCommission += Number(item.item_commission || 0); 
    });
    
    this.setData({
      'parsedData.total_item_count': totalItems,
      'parsedData.total_order_amount': totalOrderAmount,
      'parsedData.total_gifting_cost': recalculatedTotalGiftingCost,
      'parsedData.total_gifting_cost_str': recalculatedTotalGiftingCost.toFixed(2),
      'parsedData.total_commission': recalculatedTotalCommission, // 更新总提成
      'parsedData.total_commission_str': recalculatedTotalCommission.toFixed(2), // 格式化显示
    });
  },

  async onSaveOrderTap() {
    console.log("onSaveOrderTap 函数被触发！"); // <--- 添加这行代码
    if (!this.data.parsedData || !this.data.parsedData.order_items || this.data.parsedData.order_items.length === 0) {
      wx.showToast({ title: '这是一个无效订单，至少需要包含一个产品！', icon: 'none' });
      return;
    }
    this.setData({ isLoading: true });
    const saveData = {
      customer_name: this.data.parsedData.customer_name,
      order_date: this.data.selectedDate,
      original_text: this.data.rawText,
      order_items: this.data.parsedData.order_items.map(item => ({
          product_name: item.product_name,
          quantity: Number(item.quantity),
          actual_unit_price: Number(item.actual_unit_price),
          item_amount: Number(item.item_amount),
          item_gifting_cost: Number(item.item_gifting_cost)
      })),
      display_fee: Number(this.data.parsedData.display_fee || 0),
      old_goods_disposal_fee: Number(this.data.parsedData.old_goods_disposal_fee || 0),
      gifting_cost: Number(this.data.parsedData.total_gifting_cost || 0),
      total_gifting_cost: Number(this.data.parsedData.total_gifting_cost || 0),
      other_expenses: Number(this.data.parsedData.other_expenses || 0)
    };
    try {
      const result = await requestWithAuth({ url: '/api/save_order', method: 'POST', data: saveData });
      wx.showToast({ title: '订单保存成功！', icon: 'success' });
      setTimeout(() => { wx.navigateBack(); }, 1500);
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' });
      console.error('保存失败', error);
    } finally {
      this.setData({ isLoading: false });
    }
  },

  onAddItemTap() {
    this.setData({ showAddModal: true });
  },

  closeModal() {
    this.setData({
      showAddModal: false,
      searchKeyword: '',
      searchResult: [],
      selectedProduct: null,
      newItemQuantity: '',
      newItemPrice: '',
      focusedInput: ''
    });
  },

  onSearchInput(e) {
    const keyword = e.detail.value.toLowerCase();
    this.setData({ searchKeyword: keyword });

    if (!keyword) {
      this.setData({ searchResult: [], selectedProduct: null });
      return;
    }

    const result = this.data.allProducts.filter(p => p.name.toLowerCase().includes(keyword));
    this.setData({ searchResult: result });
  },

  clearSearchInput() {
    this.setData({
      searchKeyword: '',
      searchResult: [],
      selectedProduct: null,
      newItemQuantity: '',
      newItemPrice: ''
    });
  },

  onSelectProduct(e) {
    const selected = e.currentTarget.dataset.item;
    this.setData({
      selectedProduct: selected,
      searchKeyword: selected.name,
      searchResult: [],
      newItemPrice: selected.unit_price.toFixed(2) // 默认填充产品原价
    });
  },

  onNewItemInput(e) {
    const field = e.currentTarget.dataset.field;
    let value = e.detail.value;

    if (field === 'newItemQuantity') {
      value = value.replace(/[^\d]/g, '');
      if (parseInt(value) < 0) value = '0';
    } else if (field === 'newItemPrice') {
      value = value.replace(/[^\d.]/g, '');
      value = value.replace(/\.{2,}/g, '.');
      if (value.indexOf('.') > -1 && value.split('.')[1].length > 2) {
          value = parseFloat(value).toFixed(2);
      }
      if (parseFloat(value) < 0) value = '0';
    }
    
    if (field === 'newItemQuantity') {
      this.setData({ newItemQuantity: value });
    } else if (field === 'newItemPrice') {
      this.setData({ newItemPrice: value });
    }
  },

  onNewItemConfirm() {
    const { selectedProduct, newItemQuantity, newItemPrice, parsedData } = this.data;

    if (!selectedProduct) {
      wx.showToast({ title: '请选择一个产品', icon: 'none' });
      return;
    }
    if (!newItemQuantity || Number(newItemQuantity) <= 0) {
      wx.showToast({ title: '请输入有效数量', icon: 'none' });
      return;
    }

    const quantity = parseInt(newItemQuantity);
    const actual_price = parseFloat(newItemPrice) || parseFloat(selectedProduct.unit_price);
    const unit_price = parseFloat(selectedProduct.unit_price);
    const commissionPerItem = parseFloat(selectedProduct.commission_per_item);

    const item_gifting_cost = Math.max(0, (unit_price - actual_price)) * quantity;
    const item_commission = commissionPerItem * quantity; // 单项提成

    const newItem = {
      product_name: selectedProduct.name,
      quantity: quantity,
      actual_unit_price: actual_price,
      item_amount: actual_price * quantity,
      item_gifting_cost: item_gifting_cost,
      item_commission: item_commission, // 添加单项提成
      actual_unit_price_str: actual_price.toFixed(2),
      item_gifting_cost_str: item_gifting_cost.toFixed(2)
    };

    let currentItems = parsedData.order_items || [];
    currentItems.push(newItem);

    this.setData({
      'parsedData.order_items': currentItems
    }, () => {
      this.recalculateTotals();
    });
    this.closeModal();
  },

  onInputFocus: function(e) {
    this.setData({ focusedInput: e.currentTarget.dataset.field });
  },

  onInputBlur: function() {
    this.setData({ focusedInput: '' });
  },
});
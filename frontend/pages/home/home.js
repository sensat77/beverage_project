// pages/home/home.js (移除“不展示任何产品”选项)
import { requestWithAuth } from '../../utils/api.js';

const formatDate = date => {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

Page({
  data: {
    summaryData: null,
    userInfo: null, 
    isLoading: true, // 页面整体加载状态
    selectedDate: formatDate(new Date()), // 默认选中今天

    topProductsSales: [], // 重点产品销售数据
    
    // 用于自主选择重点产品的功能
    showProductSelector: false, // 控制选择产品弹窗显示
    allAvailableProducts: [], // 所有可供选择的产品名称列表
    tempSelectedProducts: [], // 临时存储用户在弹窗中的选择
    currentSelectedProducts: [], // 用户当前已保存的重点产品列表（后端返回的）
  },

  onShow: function () {
    this.fetchData();
  },

  onPullDownRefresh: function () {
    this.fetchData(); 
  },

  onDateChange: function (e) {
    this.setData({
      selectedDate: e.detail.value
    });
    this.fetchData();
  },

  goToToday: function() {
    const today = new Date();
    const todayFormatted = formatDate(today);
    if (this.data.selectedDate !== todayFormatted) {
      this.setData({
        selectedDate: todayFormatted
      }, () => {
        this.fetchData();
      });
    } else {
      wx.showToast({
        title: '已是今日',
        icon: 'none'
      });
      this.fetchData(); 
    }
  },

  fetchData: async function () {
    this.setData({ isLoading: true });
    const date = this.data.selectedDate;
  
    try {
      const [summaryRes, profileRes, topProductsResWrapper, allProductsResWrapper] = await Promise.all([
        requestWithAuth({ url: `/api/daily_summary?date=${date}` }),
        requestWithAuth({ url: '/api/profile' }),
        requestWithAuth({ url: `/api/reports/top_product_sales?date=${date}` }), 
        requestWithAuth({ url: '/api/products/names' }) // 获取所有产品名称列表
      ]);
      
      if (summaryRes) {
        summaryRes.total_commission_str = (summaryRes.total_commission || 0).toFixed(2);
        summaryRes.total_gifting_cost_str = (summaryRes.total_gifting_cost || 0).toFixed(2);
        summaryRes.total_display_fee_str = (summaryRes.total_display_fee || 0).toFixed(2);
        summaryRes.total_old_goods_disposal_fee_str = (summaryRes.total_old_goods_disposal_fee || 0).toFixed(2);
      }

      let topProductsData = [];
      if (topProductsResWrapper && topProductsResWrapper.code === 200) {
        topProductsData = topProductsResWrapper.data || [];
      } else {
        console.error("获取重点产品销售数据失败:", topProductsResWrapper.message);
      }

      let allProductNames = [];
      if (allProductsResWrapper && allProductsResWrapper.code === 200) {
        allProductNames = allProductsResWrapper.data || [];
      } else {
        console.error("获取所有产品名称失败:", allProductsResWrapper.message);
      }

      const currentSelectedProductsFromAPI = topProductsData.map(item => item.product_name);
      
      // 如果当前没有设置任何重点产品，但allProductNames不为空，可以设置一个默认值
      // 如果需要默认选择您上次指定的“焕神”等产品，可以在这里设置
      if (currentSelectedProductsFromAPI.length === 0 && allProductNames.length > 0) {
        const defaultProducts = ["焕神", "海之言", "双萃", "绿茶", "茉莉奶绿", "春拂焙茶"];
        const validDefaultProducts = defaultProducts.filter(name => allProductNames.includes(name));
        if(validDefaultProducts.length > 0) {
          await requestWithAuth({
            url: '/api/reports/save_selected_products',
            method: 'POST',
            data: { product_names: validDefaultProducts }
          });
          const reFetchTopProductsResWrapper = await requestWithAuth({ url: `/api/reports/top_product_sales?date=${date}` });
          if(reFetchTopProductsResWrapper && reFetchTopProductsResWrapper.code === 200) {
            topProductsData = reFetchTopProductsResWrapper.data || [];
          }
          currentSelectedProductsFromAPI.splice(0, currentSelectedProductsFromAPI.length, ...validDefaultProducts);
        }
      }

      this.setData({
        summaryData: summaryRes,
        userInfo: profileRes, 
        topProductsSales: topProductsData, 
        allAvailableProducts: allProductNames, 
        currentSelectedProducts: currentSelectedProductsFromAPI, 
        isLoading: false
      });
      
    } catch (error) {
      console.error("获取首页数据失败:", error);
      wx.showToast({ title: '数据加载失败', icon: 'none' });
      this.setData({ isLoading: false });
    } finally {
      wx.stopPullDownRefresh();
    }
  },

  goToInputPage: function () {
    wx.navigateTo({
      url: '/pages/input/input'
    });
  },

  openProductSelector() {
    this.setData({
      showProductSelector: true,
      // 初始化tempSelectedProducts为当前已选产品
      tempSelectedProducts: [...this.data.currentSelectedProducts]
    });
  },

  closeProductSelector() {
    this.setData({ showProductSelector: false });
  },

  // 【移除 onProductCheckboxChange】
  // onProductCheckboxChange(e) {
  //   this.setData({ tempSelectedProducts: [...e.detail.value] }); 
  // },

  // 【新增/修改】手动处理单个产品选择的 tap 事件
  onProductItemTap: function(e) {
    const product = e.currentTarget.dataset.product; // 获取当前点击的产品名称
    let currentTempSelectedProducts = [...this.data.tempSelectedProducts]; // 复制一份当前选中列表

    const index = currentTempSelectedProducts.indexOf(product);
    if (index > -1) {
      // 如果已选中，则移除
      currentTempSelectedProducts.splice(index, 1);
    } else {
      // 如果未选中，则添加
      currentTempSelectedProducts.push(product);
    }

    this.setData({
      tempSelectedProducts: currentTempSelectedProducts // 更新数据，这将驱动 checkbox 的 checked 属性
    }, () => {
      // 可选：在回调中打印，确认数据已更新
      // console.log("tempSelectedProducts after tap:", this.data.tempSelectedProducts);
    });
  },

  confirmProductSelection: async function() {
    const selectedProducts = this.data.tempSelectedProducts;
    const finalSelection = selectedProducts; 

    try {
        const res = await requestWithAuth({
            url: '/api/reports/save_selected_products',
            method: 'POST',
            data: { product_names: finalSelection }
        });

        if (res && res.code === 200) {
            wx.showToast({ title: '重点产品设置成功', icon: 'success' });
            this.setData({
                currentSelectedProducts: finalSelection, 
                showProductSelector: false 
            });
            this.fetchData(); 
        } else {
            wx.showToast({ title: res.message || '保存失败', icon: 'none' });
        }
    } catch (error) {
        console.error("保存重点产品失败:", error);
        wx.showToast({ title: '网络错误，保存失败', icon: 'none' });
    }
  },

  navigateToDailyOrders: function() {
    wx.navigateTo({ url: '/pages/daily_orders/daily_orders' });
  },
  navigateToReport: function() {
    wx.navigateTo({ url: '/pages/report/report' });
  },
  navigateToProfile: function() {
    wx.navigateTo({ url: '/pages/profile/profile' });
  },
})
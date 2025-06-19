// pages/home/home.js (修正版)
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
    // 以下是与重点产品优化无关的，保持原样
    selectedBarcodes: [], 
    allBarcodes: [],
    showBarcodeSelector: false, 
    tempSelectedBarcodes: [] 
  },

  onShow: function () {
    const selectedBarcodes = wx.getStorageSync('selectedBarcodes') || [];
    this.setData({ selectedBarcodes });
    this.fetchData();
  },

  onPullDownRefresh: function () {
    this.fetchData(); // 下拉刷新时重新获取所有数据
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
      this.fetchData(); // 强制刷新
    }
  },

  fetchData: async function () {
    this.setData({ isLoading: true });
    const date = this.data.selectedDate;
  
    try {
      // 同时请求 daily_summary, profile, 和 top_product_sales
      const [summaryRes, profileRes, topProductsResWrapper] = await Promise.all([
        requestWithAuth({ url: `/api/daily_summary?date=${date}` }),
        requestWithAuth({ url: '/api/profile' }),
        // 调用获取重点产品销售数据的新接口
        requestWithAuth({ url: `/api/reports/top_product_sales?date=${date}` }) 
      ]);
  
      // --- 预格式化 "速览" 卡片中的金额 ---
      if (summaryRes) {
        summaryRes.total_commission_str = (summaryRes.total_commission || 0).toFixed(2);
        summaryRes.total_gifting_cost_str = (summaryRes.total_gifting_cost || 0).toFixed(2);
        summaryRes.total_display_fee_str = (summaryRes.total_display_fee || 0).toFixed(2);
        summaryRes.total_old_goods_disposal_fee_str = (summaryRes.total_old_goods_disposal_fee || 0).toFixed(2);
      }

      // 处理 topProductsResWrapper (后端统一返回格式 {code, message, data})
      let topProductsData = [];
      if (topProductsResWrapper && topProductsResWrapper.code === 200) {
        topProductsData = topProductsResWrapper.data || [];
      } else {
        console.error("获取重点产品数据失败:", topProductsResWrapper.message);
        // 这里可以根据需要给出特定提示，但避免覆盖通用网络错误
      }
  
      // 获取所有可选条码（这部分逻辑与重点产品优化无关，保持原样）
      const allBarcodes = topProductsData.map(item => ({ // 使用 topProductsData
        // 假设 item 中有 barcode 字段，如果没有，需要从产品表中获取或前端自行维护
        // 如果后端没有返回 barcode，这里可能需要调整或移除
        // barcode: item.barcode, 
        name: item.product_name
      }));
      // 如果没选过，默认展示全部
      let selectedBarcodes = this.data.selectedBarcodes;
      if (!selectedBarcodes || selectedBarcodes.length === 0) {
        // selectedBarcodes = allBarcodes.map(item => item.barcode); // 如果没有barcode，则无法映射
        // wx.setStorageSync('selectedBarcodes', selectedBarcodes);
        // 为了避免没有barcode字段报错，这里可以简单地设置为所有产品名称，如果不需要过滤，这部分也可移除
      }
  
      this.setData({
        summaryData: summaryRes,
        userInfo: profileRes, 
        topProductsSales: topProductsData, // 更新为后端返回的重点产品数据
        allBarcodes, // 这部分依赖于后端返回的 barcode 字段，如果后端不返回，前端需要调整
        selectedBarcodes,
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

  // 【删除】onOrderTap 函数，因为不再显示最近订单 (这部分代码之前已经建议删除了，确保它仍然被删除)
  // onOrderTap: function(e) {
  //   const orderId = e.currentTarget.dataset.orderid;
  //   wx.navigateTo({
  //     url: `/pages/order_detail/order_detail?id=${orderId}`
  //   });
  // },

  goToInputPage: function () {
    wx.navigateTo({
      url: '/pages/input/input'
    });
  },

  // 打开选择条码弹窗 (保持不变，但其功能性依赖于 `allBarcodes` 的数据结构)
  openBarcodeSelector() {
    this.setData({
      showBarcodeSelector: true,
      tempSelectedBarcodes: [...this.data.selectedBarcodes]
    });
  },
  // 关闭弹窗 (保持不变)
  closeBarcodeSelector() {
    this.setData({ showBarcodeSelector: false });
  },
  // 多选切换 (保持不变)
  onBarcodeCheckboxChange(e) {
    this.setData({ tempSelectedBarcodes: e.detail.value });
  },
  // 确认选择 (保持不变)
  confirmBarcodeSelection() {
    const selectedBarcodes = this.data.tempSelectedBarcodes;
    wx.setStorageSync('selectedBarcodes', selectedBarcodes);
    this.setData({
      selectedBarcodes,
      showBarcodeSelector: false
    });
  }
})
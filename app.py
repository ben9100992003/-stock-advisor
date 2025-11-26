<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>實價登錄資料</title>
  <style>
    body {
      margin: 0;
      padding: 20px 30px 40px;
      background: #f5f5f5;
      font-family: "標楷體","Microsoft JhengHei",sans-serif;
    }
    .top-bar {
      text-align: right;
      margin-bottom: 10px;
    }
    .btn-back {
      padding: 6px 14px;
      border-radius: 4px;
      border: 1px solid #999;
      background: #fff;
      cursor: pointer;
      font-size: 13px;
    }
    .page-title {
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 10px;
      margin: 0 0 10px;
    }

    .container {
      max-width: 1920px;
      margin: 0 auto;
    }

    .flex-row {
      display: flex;
      gap: 20px;
      align-items: flex-start;
    }
    .card {
      background: #fff;
      border-radius: 6px;
      box-shadow: 0 0 4px rgba(0,0,0,0.15);
      padding: 15px 18px 18px;
      flex: 1;
    }
    .card-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .card-title {
      font-size: 20px;
      font-weight: 700;
    }

    .btn-green {
      padding: 6px 16px;
      border-radius: 4px;
      border: none;
      background: #2e7d32;
      color: #fff;
      cursor: pointer;
      font-size: 14px;
    }
    .btn-green:hover { background:#256628; }

    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 13px;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 6px 4px;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    thead th {
      background: #556b2f;
      color: #fff;
      font-weight: 600;
    }
    .col-addr { text-align: left; padding-left: 8px; }
    .col-total, .col-unit { color:#ff6b00; font-weight:700; }

    .btn-blue {
      padding: 4px 12px;
      border-radius: 4px;
      border: none;
      background: #1976d2;
      color: #fff;
      cursor: pointer;
      font-size: 13px;
    }
    .btn-blue:hover { background:#145ca6; }

    .avg-info {
      margin-top: 8px;
      font-size: 14px;
    }

    .btn-more-wrapper{
      text-align:center;
      margin-top:16px;
    }
    .btn-more{
      padding:8px 40px;
      border-radius:4px;
      border:1px solid #999;
      background:#fff;
      cursor:pointer;
      font-size:14px;
    }
  </style>
</head>
<body>
<div class="container">

  <div class="top-bar">
    <button class="btn-back" onclick="location.href='search.html'">返回搜尋</button>
  </div>

  <h1 class="page-title">實 價 登 錄 資 料</h1>

  <div class="flex-row">
    <!-- 左邊：實價登錄 -->
    <div class="card">
      <div class="card-title-row">
        <div class="card-title">實價登錄資料</div>
        <button id="importBtn" class="btn-green">匯入資料</button>
      </div>

      <table>
        <thead>
        <tr>
          <th style="width:40px;">勾選</th>
          <th style="width:90px;">成交年月</th>
          <th>地址</th>
          <th style="width:60px;">型態</th>
          <th style="width:80px;">總價</th>
          <th style="width:90px;">單價</th>
          <th style="width:80px;">建坪</th>
          <th style="width:80px;">地坪</th>
          <th style="width:80px;">樓別</th>
          <th style="width:60px;">屋齡</th>
          <th style="width:70px;">內容</th>
        </tr>
        </thead>
        <tbody>
        <!-- 1 -->
        <tr data-unit="39.5">
          <td><input type="checkbox" class="select-row"></td>
          <td class="col-date">111年12月</td>
          <td class="col-addr">北區德化街350號</td>
          <td class="col-type">透天</td>
          <td class="col-total">950萬</td>
          <td class="col-unit">39.5萬/坪</td>
          <td class="col-build">15.13坪</td>
          <td class="col-land">9.00坪</td>
          <td class="col-floor">1-2/2</td>
          <td class="col-age">5.2年</td>
          <td><button class="btn-blue" onclick="location.href='detail_house.html'">明細</button></td>
        </tr>
        <!-- 2 -->
        <tr data-unit="34.4">
          <td><input type="checkbox" class="select-row"></td>
          <td class="col-date">111年12月</td>
          <td class="col-addr">北區德化街150號</td>
          <td class="col-type">透天</td>
          <td class="col-total">3,790萬</td>
          <td class="col-unit">34.4萬/坪</td>
          <td class="col-build">110.05坪</td>
          <td class="col-land">75.87坪</td>
          <td class="col-floor">1-5/5</td>
          <td class="col-age">4.0年</td>
          <td><button class="btn-blue" onclick="location.href='detail_house.html'">明細</button></td>
        </tr>
        <!-- 3 -->
        <tr data-unit="26.9">
          <td><input type="checkbox" class="select-row"></td>
          <td class="col-date">111年11月</td>
          <td class="col-addr">北區德化街571號</td>
          <td class="col-type">透天</td>
          <td class="col-total">1,800萬</td>
          <td class="col-unit">26.9萬/坪</td>
          <td class="col-build">67.04坪</td>
          <td class="col-land">40.42坪</td>
          <td class="col-floor">1-3/3</td>
          <td class="col-age">4.9年</td>
          <td><button class="btn-blue" onclick="location.href='detail_house.html'">明細</button></td>
        </tr>
        <!-- 4 -->
        <tr data-unit="42.8">
          <td><input type="checkbox" class="select-row"></td>
          <td class="col-date">111年09月</td>
          <td class="col-addr">北區德化街384號</td>
          <td class="col-type">透天</td>
          <td class="col-total">1,230萬</td>
          <td class="col-unit">42.8萬/坪</td>
          <td class="col-build">28.71坪</td>
          <td class="col-land">17.24坪</td>
          <td class="col-floor">1-2/2</td>
          <td class="col-age">4.8年</td>
          <td><button class="btn-blue" onclick="location.href='detail_house.html'">明細</button></td>
        </tr>
        <!-- 5 -->
        <tr data-unit="50.3">
          <td><input type="checkbox" class="select-row"></td>
          <td class="col-date">111年07月</td>
          <td class="col-addr">北區德化街406號</td>
          <td class="col-type">透天</td>
          <td class="col-total">2,968萬</td>
          <td class="col-unit">50.3萬/坪</td>
          <td class="col-build">59.01坪</td>
          <td class="col-land">38.12坪</td>
          <td class="col-floor">1-2/2</td>
          <td class="col-age">5.0年</td>
          <td><button class="btn-blue" onclick="location.href='detail_house.html'">明細</button></td>
        </tr>
        </tbody>
      </table>

      <div id="avgInfo" class="avg-info">尚未選擇資料</div>
    </div>

    <!-- 右邊：本行資料庫 -->
    <div class="card">
      <div class="card-title-row">
        <div class="card-title">本行資料庫</div>
      </div>
      <table>
        <thead>
        <tr>
          <th>鑑估標的</th>
          <th style="width:120px;">申請日期</th>
          <th style="width:150px;">估價完成時間</th>
          <th style="width:80px;">功能</th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <td>台中市北區錦祥街334-6號</td>
          <td>114/11/13</td>
          <td>114/11/19 12:54</td>
          <td><button class="btn-blue" onclick="window.open('#','_blank')">查詢</button></td>
        </tr>
        <tr>
          <td>台中市北區德澤子段90-4號</td>
          <td>113/01/16</td>
          <td>113/02/15 13:42</td>
          <td><button class="btn-blue" onclick="window.open('#','_blank')">查詢</button></td>
        </tr>
        <tr>
          <td>台中市北區德化街62號</td>
          <td>112/11/01</td>
          <td>112/11/20 15:08</td>
          <td><button class="btn-blue" onclick="window.open('#','_blank')">查詢</button></td>
        </tr>
        <tr>
          <td>台中市北區德化街213-30號</td>
          <td>112/07/05</td>
          <td>112/07/20 11:09</td>
          <td><button class="btn-blue" onclick="window.open('#','_blank')">查詢</button></td>
        </tr>
        <tr>
          <td>台中市北區德化街100號</td>
          <td>111/05/20</td>
          <td>111/06/01 10:30</td>
          <td><button class="btn-blue" onclick="window.open('#','_blank')">查詢</button></td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="btn-more-wrapper">
    <button class="btn-more">顯示更多</button>
  </div>

</div>

<script>
  document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = document.querySelectorAll('.select-row');
    const avgInfo = document.getElementById('avgInfo');

    // 計算平均單價
    function updateAverage() {
      let count = 0;
      let sum = 0;
      checkboxes.forEach(cb => {
        if (cb.checked) {
          count++;
          const tr = cb.closest('tr');
          const unit = parseFloat(tr.dataset.unit);  // data-unit
          if (!isNaN(unit)) sum += unit;
        }
      });

      if (count === 0) {
        avgInfo.textContent = '尚未選擇資料';
      } else {
        const avg = (sum / count).toFixed(1);
        avgInfo.textContent = `已選取 ${count} 筆資料，單坪平均價格：${avg} 萬/坪`;
      }
    }

    checkboxes.forEach(cb => cb.addEventListener('change', updateAverage));
    updateAverage(); // 初始化

    // 匯入資料：將選取資料存進 localStorage，再跳到 common.html
    const importBtn = document.getElementById('importBtn');
    importBtn.addEventListener('click', function () {
      const selectedRows = [];
      checkboxes.forEach(cb => {
        if (cb.checked) {
          const tr = cb.closest('tr');
          selectedRows.push({
            date: tr.querySelector('.col-date').innerText.trim(),
            addr: tr.querySelector('.col-addr').innerText.trim(),
            type: tr.querySelector('.col-type').innerText.trim(),
            total: tr.querySelector('.col-total').innerText.trim(),
            unit: tr.querySelector('.col-unit').innerText.trim(),
            build: tr.querySelector('.col-build').innerText.trim(),
            land: tr.querySelector('.col-land').innerText.trim(),
            floor: tr.querySelector('.col-floor').innerText.trim(),
            age: tr.querySelector('.col-age').innerText.trim()
          });
        }
      });

      if (selectedRows.length === 0) {
        alert('請先勾選要匯入的資料。');
        return;
      }

      // 存到 localStorage，common.html 再去讀
      localStorage.setItem('houseSelected', JSON.stringify(selectedRows));
      window.location.href = 'common.html';  // 如果你的共用表頁面叫別的名字，這裡改掉即可
    });
  });
</script>
</body>
</html>

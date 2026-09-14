CREATE DATABASE IF NOT EXISTS supply_chain_ai
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE supply_chain_ai;

DROP TABLE IF EXISTS purchase_detail;
DROP TABLE IF EXISTS supplier;

CREATE TABLE supplier (
    supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL
);

CREATE TABLE purchase_detail (
    purchase_detail_id INT PRIMARY KEY,
    order_no VARCHAR(30) NOT NULL,
    order_date DATE NOT NULL,
    supplier_id INT NOT NULL,
    material_code VARCHAR(30) NOT NULL,
    material_name VARCHAR(100) NOT NULL,
    purchase_qty DECIMAL(18,2) NOT NULL,
    unit_price DECIMAL(18,2) NOT NULL,
    received_qty DECIMAL(18,2) NOT NULL,
    warehouse_date DATE NULL,
    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

INSERT INTO supplier (supplier_id, supplier_name) VALUES
(1, '大地集市'),
(2, '金蝶蓝海实业集团'),
(3, '华北工业供应链'),
(4, '中原物资有限公司'),
(5, '河南佳采商贸');

INSERT INTO purchase_detail
(purchase_detail_id, order_no, order_date, supplier_id, material_code, material_name,
 purchase_qty, unit_price, received_qty, warehouse_date)
VALUES
(1, 'CG752609', '2026-08-01', 1, '156202', '测试物料A', 500, 12.00, 500, '2026-08-03'),
(2, 'CG752609', '2026-08-01', 1, '156203', '测试物料B', 300, 8.00, 300, '2026-08-04'),
(3, 'CG752610', '2026-08-02', 2, '156204', '测试物料C', 800, 15.00, 820, '2026-08-05'),
(4, 'CG752611', '2026-08-05', 2, '156205', '测试物料D', 200, 25.00, 200, '2026-08-07'),
(5, 'CG752612', '2026-08-08', 3, '156206', '测试物料E', 1000, 6.50, 950, '2026-08-12'),
(6, 'CG752613', '2026-08-12', 4, '156207', '测试物料F', 600, 11.00, 600, '2026-08-14'),
(7, 'CG752614', '2026-08-15', 5, '156208', '测试物料G', 400, 18.00, 450, '2026-08-18'),
(8, 'CG752615', '2026-08-20', 1, '156209', '测试物料H', 700, 9.00, 700, '2026-08-23'),
(9, 'CG752616', '2026-08-22', 3, '156210', '测试物料I', 300, 30.00, 300, '2026-08-25'),
(10, 'CG752617', '2026-08-25', 2, '156211', '测试物料J', 900, 7.00, 900, '2026-08-28');

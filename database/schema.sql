-- =====================================================================
-- OTEL REZERVASYON VE KONAKLAMA YONETIM SISTEMI
-- MySQL 8.0.16+ icin (CHECK kisitlari ve recursive CTE kullanilir)
--
-- Calistirma:
--   Workbench: File > Open SQL Script > yildirim simgesi (tumunu calistir)
--   Terminal : mysql -u root -p < schema.sql
--
-- DIKKAT: Betik her calistirildiginda otel_db'yi SIFIRDAN olusturur
-- (varsa onceki veritabani silinir). Gelistirme asamasi icin boyle birakildi.
-- =====================================================================

SET NAMES utf8mb4;

DROP DATABASE IF EXISTS otel_db;
CREATE DATABASE otel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_turkish_ci;
USE otel_db;

-- =====================================================================
-- 1) TABLOLAR (3NF)
-- =====================================================================

CREATE TABLE OdaTipi (
    tip_id        INT AUTO_INCREMENT PRIMARY KEY,
    tip_adi       VARCHAR(30)   NOT NULL UNIQUE,          -- standart, deluxe, suit
    kapasite      TINYINT       NOT NULL,
    aciklama      VARCHAR(255),
    temel_fiyat   DECIMAL(10,2) NOT NULL,                 -- sezon fiyati yoksa bu uygulanir
    CONSTRAINT ck_tip_kapasite CHECK (kapasite > 0),
    CONSTRAINT ck_tip_fiyat    CHECK (temel_fiyat >= 0)
) ENGINE=InnoDB;

CREATE TABLE Oda (
    oda_id   INT AUTO_INCREMENT PRIMARY KEY,
    oda_no   VARCHAR(10) NOT NULL UNIQUE,
    kat      TINYINT     NOT NULL,
    tip_id   INT         NOT NULL,
    durum    ENUM('bos','dolu','temizlikte','bakimda') NOT NULL DEFAULT 'bos',
    CONSTRAINT fk_oda_tip FOREIGN KEY (tip_id) REFERENCES OdaTipi(tip_id)
) ENGINE=InnoDB;

CREATE TABLE SezonFiyati (
    sezon_id         INT AUTO_INCREMENT PRIMARY KEY,
    tip_id           INT           NOT NULL,
    baslangic_tarihi DATE          NOT NULL,
    bitis_tarihi     DATE          NOT NULL,              -- bu gun dahil
    gecelik_fiyat    DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_sezon_tip FOREIGN KEY (tip_id) REFERENCES OdaTipi(tip_id),
    CONSTRAINT ck_sezon_tarih CHECK (bitis_tarihi >= baslangic_tarihi),
    CONSTRAINT ck_sezon_fiyat CHECK (gecelik_fiyat >= 0)
) ENGINE=InnoDB;

CREATE TABLE Misafir (
    misafir_id      INT AUTO_INCREMENT PRIMARY KEY,
    ad              VARCHAR(50)  NOT NULL,
    soyad           VARCHAR(50)  NOT NULL,
    tc_pasaport_no  VARCHAR(20)  NOT NULL UNIQUE,
    telefon         VARCHAR(20),
    eposta          VARCHAR(100) NOT NULL UNIQUE,
    dogum_tarihi    DATE
) ENGINE=InnoDB;

CREATE TABLE Personel (
    personel_id       INT AUTO_INCREMENT PRIMARY KEY,
    ad                VARCHAR(50) NOT NULL,
    soyad             VARCHAR(50) NOT NULL,
    gorev             ENUM('resepsiyon','kat_gorevlisi','yonetici') NOT NULL,
    ise_giris_tarihi  DATE        NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Kullanici (
    kullanici_id  INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_adi VARCHAR(100) NOT NULL UNIQUE,           -- e-posta ile giris
    sifre_hash    VARCHAR(255) NOT NULL,                  -- asla duz metin saklanmaz
    rol           ENUM('misafir','resepsiyon','yonetici') NOT NULL,
    misafir_id    INT NULL,
    personel_id   INT NULL,
    CONSTRAINT fk_kull_misafir  FOREIGN KEY (misafir_id)  REFERENCES Misafir(misafir_id),
    CONSTRAINT fk_kull_personel FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    -- misafir rolu bir misafire, personel rolleri bir personele bagli olmali
    CONSTRAINT ck_kull_rol CHECK (
        (rol = 'misafir' AND misafir_id IS NOT NULL AND personel_id IS NULL)
        OR
        (rol IN ('resepsiyon','yonetici') AND personel_id IS NOT NULL AND misafir_id IS NULL)
    )
) ENGINE=InnoDB;

CREATE TABLE Rezervasyon (
    rezervasyon_id    INT AUTO_INCREMENT PRIMARY KEY,
    misafir_id        INT      NOT NULL,
    oda_id            INT      NOT NULL,
    giris_tarihi      DATE     NOT NULL,
    cikis_tarihi      DATE     NOT NULL,                  -- cikis gunu gecelenmez
    kisi_sayisi       TINYINT  NOT NULL DEFAULT 1,
    durum             ENUM('beklemede','onayli','iptal','tamamlandi') NOT NULL DEFAULT 'beklemede',
    olusturma_tarihi  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rez_misafir FOREIGN KEY (misafir_id) REFERENCES Misafir(misafir_id),
    CONSTRAINT fk_rez_oda     FOREIGN KEY (oda_id)     REFERENCES Oda(oda_id),
    CONSTRAINT ck_rez_tarih   CHECK (cikis_tarihi > giris_tarihi),
    CONSTRAINT ck_rez_kisi    CHECK (kisi_sayisi > 0)
) ENGINE=InnoDB;

CREATE TABLE Konaklama (
    konaklama_id      INT AUTO_INCREMENT PRIMARY KEY,
    rezervasyon_id    INT      NOT NULL UNIQUE,           -- bir rezervasyon bir kez check-in olur
    gercek_giris      DATETIME NOT NULL,
    gercek_cikis      DATETIME NULL,
    personel_id       INT      NOT NULL,                  -- check-in yapan personel
    cikis_personel_id INT      NULL,                      -- check-out yapan personel
    CONSTRAINT fk_kon_rez   FOREIGN KEY (rezervasyon_id)    REFERENCES Rezervasyon(rezervasyon_id),
    CONSTRAINT fk_kon_pers  FOREIGN KEY (personel_id)       REFERENCES Personel(personel_id),
    CONSTRAINT fk_kon_pers2 FOREIGN KEY (cikis_personel_id) REFERENCES Personel(personel_id)
) ENGINE=InnoDB;

CREATE TABLE EkHizmet (
    hizmet_id    INT AUTO_INCREMENT PRIMARY KEY,
    hizmet_adi   VARCHAR(60)    NOT NULL UNIQUE,
    birim_fiyat  DECIMAL(10,2)  NOT NULL,
    CONSTRAINT ck_hizmet_fiyat CHECK (birim_fiyat >= 0)
) ENGINE=InnoDB;

CREATE TABLE KonaklamaHizmeti (
    kh_id         INT AUTO_INCREMENT PRIMARY KEY,
    konaklama_id  INT           NOT NULL,
    hizmet_id     INT           NOT NULL,
    adet          INT           NOT NULL DEFAULT 1,
    -- Satis anindaki fiyat. Hizmetin fiyati sonradan degisse bile eski
    -- hesaplar bozulmasin diye bilerek saklanir (tarihsel kayit, turetilmis veri degil).
    birim_fiyat   DECIMAL(10,2) NOT NULL,
    tarih         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_kh_kon    FOREIGN KEY (konaklama_id) REFERENCES Konaklama(konaklama_id),
    CONSTRAINT fk_kh_hizmet FOREIGN KEY (hizmet_id)    REFERENCES EkHizmet(hizmet_id),
    CONSTRAINT ck_kh_adet   CHECK (adet > 0)
) ENGINE=InnoDB;

CREATE TABLE Odeme (
    odeme_id      INT AUTO_INCREMENT PRIMARY KEY,
    konaklama_id  INT           NOT NULL,
    tutar         DECIMAL(10,2) NOT NULL,
    odeme_turu    ENUM('nakit','kart') NOT NULL,
    tarih         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_odeme_kon  FOREIGN KEY (konaklama_id) REFERENCES Konaklama(konaklama_id),
    CONSTRAINT ck_odeme_tutar CHECK (tutar > 0)
) ENGINE=InnoDB;

CREATE TABLE TemizlikKaydi (
    temizlik_id  INT AUTO_INCREMENT PRIMARY KEY,
    oda_id       INT  NOT NULL,
    personel_id  INT  NULL,                               -- check-out aninda henuz atanmamis olabilir
    tarih        DATE NOT NULL,
    durum        ENUM('bekliyor','tamamlandi') NOT NULL DEFAULT 'bekliyor',
    CONSTRAINT fk_tem_oda  FOREIGN KEY (oda_id)      REFERENCES Oda(oda_id),
    CONSTRAINT fk_tem_pers FOREIGN KEY (personel_id) REFERENCES Personel(personel_id)
) ENGINE=InnoDB;

CREATE TABLE IslemLog (
    log_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    tablo_adi     VARCHAR(30) NOT NULL,
    islem_turu    ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    kayit_id      INT         NOT NULL,
    eski_deger    JSON NULL,
    yeni_deger    JSON NULL,
    islem_zamani  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    db_kullanici  VARCHAR(100) NOT NULL DEFAULT (CURRENT_USER())
) ENGINE=InnoDB;

-- =====================================================================
-- 2) INDEKSLER
-- (Rapordaki indeksli / indekssiz sure karsilastirmasi bunlar uzerinden yapilir.
--  Misafir.eposta ve Oda.oda_no icin UNIQUE kisiti zaten indeks olusturur.)
-- =====================================================================

CREATE INDEX idx_rez_oda_tarih ON Rezervasyon (oda_id, giris_tarihi, cikis_tarihi);
CREATE INDEX idx_rez_tarih     ON Rezervasyon (giris_tarihi, cikis_tarihi);
CREATE INDEX idx_rez_durum     ON Rezervasyon (durum);
CREATE INDEX idx_sezon_tip_tarih ON SezonFiyati (tip_id, baslangic_tarihi, bitis_tarihi);
CREATE INDEX idx_odeme_tarih   ON Odeme (tarih);
CREATE INDEX idx_log_tablo_kayit ON IslemLog (tablo_adi, kayit_id);

-- =====================================================================
-- 3) FONKSIYONLAR VE PROSEDURLER
-- =====================================================================

DELIMITER $$

-- Verilen oda tipi icin [giris, cikis) araligindaki her gecenin sezon fiyatini
-- toplar. O geceyi kapsayan sezon yoksa tipin temel fiyati kullanilir.
CREATE FUNCTION fn_oda_tutari(p_tip_id INT, p_giris DATE, p_cikis DATE)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_toplam DECIMAL(10,2);

    IF p_cikis <= p_giris THEN
        RETURN 0;
    END IF;

    SELECT COALESCE(SUM(
               COALESCE(
                   (SELECT sf.gecelik_fiyat
                      FROM SezonFiyati sf
                     WHERE sf.tip_id = p_tip_id
                       AND n.d BETWEEN sf.baslangic_tarihi AND sf.bitis_tarihi
                     ORDER BY sf.baslangic_tarihi DESC
                     LIMIT 1),
                   (SELECT ot.temel_fiyat FROM OdaTipi ot WHERE ot.tip_id = p_tip_id)
               )
           ), 0)
      INTO v_toplam
      FROM (
            WITH RECURSIVE gece(d) AS (
                SELECT p_giris
                UNION ALL
                SELECT d + INTERVAL 1 DAY FROM gece WHERE d + INTERVAL 1 DAY < p_cikis
            )
            SELECT d FROM gece
           ) AS n;

    RETURN v_toplam;
END$$

-- Bir konaklamanin oda ucreti. Cikis yapildiysa gercek cikis gunune, yapilmadiysa
-- rezervasyondaki planli cikis gunune gore hesaplanir. En az 1 gece ucretlendirilir.
CREATE FUNCTION fn_konaklama_oda_tutari(p_konaklama_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_tip    INT;
    DECLARE v_giris  DATE;
    DECLARE v_cikis  DATE;

    SELECT o.tip_id, DATE(k.gercek_giris), COALESCE(DATE(k.gercek_cikis), r.cikis_tarihi)
      INTO v_tip, v_giris, v_cikis
      FROM Konaklama k
      JOIN Rezervasyon r ON r.rezervasyon_id = k.rezervasyon_id
      JOIN Oda o         ON o.oda_id = r.oda_id
     WHERE k.konaklama_id = p_konaklama_id;

    IF v_tip IS NULL THEN
        RETURN 0;
    END IF;

    IF v_cikis <= v_giris THEN
        SET v_cikis = v_giris + INTERVAL 1 DAY;
    END IF;

    RETURN fn_oda_tutari(v_tip, v_giris, v_cikis);
END$$

CREATE FUNCTION fn_konaklama_hizmet_tutari(p_konaklama_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_toplam DECIMAL(10,2);

    SELECT COALESCE(SUM(adet * birim_fiyat), 0)
      INTO v_toplam
      FROM KonaklamaHizmeti
     WHERE konaklama_id = p_konaklama_id;

    RETURN v_toplam;
END$$

-- Rezervasyon kurallarini denetler: tarih sirasi, oda kapasitesi, tarih cakismasi.
-- Hem INSERT hem UPDATE tetikleyicisi tarafindan cagrilir.
-- Odanin satirini kilitler; boylece ayni odaya ayni anda gelen iki istek
-- siraya girer ve ikisi birden cakisma kontrolunu gecemez.
CREATE PROCEDURE sp_rezervasyon_kontrol(
    IN p_id     INT,
    IN p_oda    INT,
    IN p_giris  DATE,
    IN p_cikis  DATE,
    IN p_kisi   INT,
    IN p_durum  VARCHAR(20)
)
BEGIN
    DECLARE v_kilit    INT;
    DECLARE v_kapasite INT;
    DECLARE v_cakisma  INT DEFAULT 0;

    IF p_cikis <= p_giris THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Çıkış tarihi giriş tarihinden sonra olmalıdır.';
    END IF;

    SELECT oda_id INTO v_kilit FROM Oda WHERE oda_id = p_oda FOR UPDATE;

    SELECT ot.kapasite INTO v_kapasite
      FROM Oda o JOIN OdaTipi ot ON ot.tip_id = o.tip_id
     WHERE o.oda_id = p_oda;

    IF p_kisi > v_kapasite THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Kişi sayısı oda kapasitesini aşıyor.';
    END IF;

    IF p_durum IN ('beklemede','onayli') THEN
        SELECT COUNT(*) INTO v_cakisma
          FROM Rezervasyon
         WHERE oda_id = p_oda
           AND rezervasyon_id <> IFNULL(p_id, 0)
           AND durum IN ('beklemede','onayli')
           AND giris_tarihi < p_cikis
           AND cikis_tarihi > p_giris;

        IF v_cakisma > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bu oda seçilen tarihlerde zaten rezerve edilmiş.';
        END IF;
    END IF;
END$$

-- PROSEDUR 1: Tarih araligi ve oda tipine gore bos odalar.
-- p_tip_id ve p_kisi NULL verilirse o filtre uygulanmaz.
CREATE PROCEDURE sp_bos_odalar(
    IN p_giris  DATE,
    IN p_cikis  DATE,
    IN p_tip_id INT,
    IN p_kisi   INT
)
BEGIN
    IF p_cikis <= p_giris THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Çıkış tarihi giriş tarihinden sonra olmalıdır.';
    END IF;

    SELECT o.oda_id,
           o.oda_no,
           o.kat,
           ot.tip_id,
           ot.tip_adi,
           ot.kapasite,
           ot.aciklama,
           DATEDIFF(p_cikis, p_giris)                    AS gece_sayisi,
           fn_oda_tutari(ot.tip_id, p_giris, p_cikis)    AS toplam_tutar
      FROM Oda o
      JOIN OdaTipi ot ON ot.tip_id = o.tip_id
     WHERE (p_tip_id IS NULL OR o.tip_id = p_tip_id)
       AND (p_kisi   IS NULL OR ot.kapasite >= p_kisi)
       AND o.durum <> 'bakimda'
       AND NOT EXISTS (
             SELECT 1
               FROM Rezervasyon r
              WHERE r.oda_id = o.oda_id
                AND r.durum IN ('beklemede','onayli')
                AND r.giris_tarihi < p_cikis
                AND r.cikis_tarihi > p_giris
           )
     ORDER BY ot.tip_adi, o.oda_no;
END$$

-- PROSEDUR 2: Bir konaklamanin toplam tutari (sezon fiyatlari + ek hizmetler).
CREATE PROCEDURE sp_konaklama_tutari(IN p_konaklama_id INT)
BEGIN
    DECLARE v_oda     DECIMAL(10,2);
    DECLARE v_hizmet  DECIMAL(10,2);
    DECLARE v_odenen  DECIMAL(10,2);

    SET v_oda    = fn_konaklama_oda_tutari(p_konaklama_id);
    SET v_hizmet = fn_konaklama_hizmet_tutari(p_konaklama_id);

    SELECT COALESCE(SUM(tutar), 0) INTO v_odenen
      FROM Odeme WHERE konaklama_id = p_konaklama_id;

    SELECT p_konaklama_id            AS konaklama_id,
           v_oda                     AS oda_tutari,
           v_hizmet                  AS hizmet_tutari,
           v_oda + v_hizmet          AS toplam_tutar,
           v_odenen                  AS odenen_tutar,
           GREATEST(v_oda + v_hizmet - v_odenen, 0) AS kalan_tutar;
END$$

-- PROSEDUR 3: Aylik doluluk orani ve gelir raporu.
-- Doluluk = (onayli/tamamlanan rezervasyonlarin aya dusen oda-geceleri)
--           / (toplam oda sayisi x ayin gun sayisi)
CREATE PROCEDURE sp_aylik_rapor(IN p_yil INT, IN p_ay INT)
BEGIN
    DECLARE v_bas       DATE;
    DECLARE v_son       DATE;       -- sonraki ayin ilk gunu
    DECLARE v_gun       INT;
    DECLARE v_oda_say   INT;
    DECLARE v_dolu_gece INT;
    DECLARE v_gelir     DECIMAL(12,2);

    IF p_ay < 1 OR p_ay > 12 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ay 1 ile 12 arasında olmalıdır.';
    END IF;

    SET v_bas = STR_TO_DATE(CONCAT(p_yil, '-', LPAD(p_ay, 2, '0'), '-01'), '%Y-%m-%d');
    SET v_son = v_bas + INTERVAL 1 MONTH;
    SET v_gun = DATEDIFF(v_son, v_bas);

    SELECT COUNT(*) INTO v_oda_say FROM Oda;

    SELECT COALESCE(SUM(GREATEST(0,
               DATEDIFF(LEAST(cikis_tarihi, v_son), GREATEST(giris_tarihi, v_bas)))), 0)
      INTO v_dolu_gece
      FROM Rezervasyon
     WHERE durum IN ('onayli','tamamlandi')
       AND giris_tarihi < v_son
       AND cikis_tarihi > v_bas;

    SELECT COALESCE(SUM(tutar), 0) INTO v_gelir
      FROM Odeme
     WHERE tarih >= v_bas AND tarih < v_son;

    SELECT p_yil                         AS yil,
           p_ay                          AS ay,
           v_oda_say                     AS toplam_oda,
           v_oda_say * v_gun             AS mumkun_oda_gecesi,
           v_dolu_gece                   AS dolu_oda_gecesi,
           IF(v_oda_say = 0, 0, ROUND(v_dolu_gece / (v_oda_say * v_gun) * 100, 2)) AS doluluk_orani,
           v_gelir                       AS gelir;
END$$

-- CHECK-IN: rezervasyon onayli ve oda bos olmali. Odanin 'dolu' olmasini
-- trg_konaklama_checkin tetikleyicisi yapar.
CREATE PROCEDURE sp_checkin(
    IN  p_rezervasyon_id INT,
    IN  p_personel_id    INT,
    OUT p_konaklama_id   INT
)
BEGIN
    DECLARE v_durum      VARCHAR(20);
    DECLARE v_oda_durum  VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT r.durum, o.durum INTO v_durum, v_oda_durum
      FROM Rezervasyon r
      JOIN Oda o ON o.oda_id = r.oda_id
     WHERE r.rezervasyon_id = p_rezervasyon_id
       FOR UPDATE;

    IF v_durum IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rezervasyon bulunamadı.';
    END IF;
    IF v_durum <> 'onayli' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Yalnızca onaylı rezervasyonla check-in yapılabilir.';
    END IF;
    IF v_oda_durum <> 'bos' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Oda şu an müsait değil (dolu, temizlikte veya bakımda).';
    END IF;

    INSERT INTO Konaklama (rezervasyon_id, gercek_giris, personel_id)
    VALUES (p_rezervasyon_id, NOW(), p_personel_id);

    SET p_konaklama_id = LAST_INSERT_ID();

    COMMIT;
END$$

-- CHECK-OUT (TRANSACTION): konaklama kapatilir, odeme kaydedilir, oda durumu
-- guncellenir. Herhangi bir adim hata verirse hepsi ROLLBACK ile geri alinir.
--   * Oda 'temizlikte' ve rezervasyon 'tamamlandi' olur: trg_konaklama_checkout.
--   * p_test_hata = 1 verilirse islemin sonunda bilerek hata uretilir; boylece
--     videoda ROLLBACK'in tum adimlari geri aldigi gosterilebilir.
CREATE PROCEDURE sp_checkout(
    IN  p_konaklama_id INT,
    IN  p_personel_id  INT,
    IN  p_odeme_turu   VARCHAR(10),
    IN  p_test_hata    TINYINT,
    OUT p_odenecek     DECIMAL(10,2)
)
BEGIN
    DECLARE v_acik    INT DEFAULT 0;
    DECLARE v_toplam  DECIMAL(10,2);
    DECLARE v_odenen  DECIMAL(10,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT COUNT(*) INTO v_acik
      FROM Konaklama
     WHERE konaklama_id = p_konaklama_id AND gercek_cikis IS NULL
       FOR UPDATE;

    IF v_acik = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Açık konaklama bulunamadı (yok ya da zaten çıkış yapılmış).';
    END IF;

    -- 1) Konaklamayi kapat (oda ve rezervasyon durumunu tetikleyici gunceller)
    UPDATE Konaklama
       SET gercek_cikis = NOW(), cikis_personel_id = p_personel_id
     WHERE konaklama_id = p_konaklama_id;

    -- 2) Toplam tutari hesapla, daha once alinan odemeleri dus
    SET v_toplam = fn_konaklama_oda_tutari(p_konaklama_id)
                 + fn_konaklama_hizmet_tutari(p_konaklama_id);

    SELECT COALESCE(SUM(tutar), 0) INTO v_odenen
      FROM Odeme WHERE konaklama_id = p_konaklama_id;

    SET p_odenecek = GREATEST(v_toplam - v_odenen, 0);

    -- 3) Odemeyi kaydet
    IF p_odenecek > 0 THEN
        INSERT INTO Odeme (konaklama_id, tutar, odeme_turu)
        VALUES (p_konaklama_id, p_odenecek, p_odeme_turu);
    END IF;

    -- Demo icin: bilerek hata uret -> yukaridaki her sey geri alinir
    IF p_test_hata = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TEST: Check-out sırasında hata oluştu, işlem geri alındı.';
    END IF;

    COMMIT;
END$$

-- =====================================================================
-- 4) TETIKLEYICILER
-- =====================================================================

-- ---- TRIGGER 1: Cakisan tarihli rezervasyonu engelle ------------------
CREATE TRIGGER trg_rez_cakisma_ins
BEFORE INSERT ON Rezervasyon
FOR EACH ROW
BEGIN
    CALL sp_rezervasyon_kontrol(NULL, NEW.oda_id, NEW.giris_tarihi, NEW.cikis_tarihi,
                                NEW.kisi_sayisi, NEW.durum);
END$$

CREATE TRIGGER trg_rez_cakisma_upd
BEFORE UPDATE ON Rezervasyon
FOR EACH ROW
BEGIN
    CALL sp_rezervasyon_kontrol(OLD.rezervasyon_id, NEW.oda_id, NEW.giris_tarihi,
                                NEW.cikis_tarihi, NEW.kisi_sayisi, NEW.durum);
END$$

-- ---- TRIGGER 2: Check-in / check-out'ta oda durumu --------------------
-- Check-in  -> oda 'dolu'
CREATE TRIGGER trg_konaklama_checkin
AFTER INSERT ON Konaklama
FOR EACH ROW
BEGIN
    UPDATE Oda
       SET durum = 'dolu'
     WHERE oda_id = (SELECT oda_id FROM Rezervasyon WHERE rezervasyon_id = NEW.rezervasyon_id);
END$$

-- Check-out -> oda 'temizlikte', rezervasyon 'tamamlandi', temizlik kaydi acilir
CREATE TRIGGER trg_konaklama_checkout
AFTER UPDATE ON Konaklama
FOR EACH ROW
BEGIN
    DECLARE v_oda INT;

    IF OLD.gercek_cikis IS NULL AND NEW.gercek_cikis IS NOT NULL THEN
        SELECT oda_id INTO v_oda
          FROM Rezervasyon WHERE rezervasyon_id = NEW.rezervasyon_id;

        UPDATE Oda SET durum = 'temizlikte' WHERE oda_id = v_oda;

        UPDATE Rezervasyon SET durum = 'tamamlandi'
         WHERE rezervasyon_id = NEW.rezervasyon_id;

        INSERT INTO TemizlikKaydi (oda_id, personel_id, tarih, durum)
        VALUES (v_oda, NULL, CURDATE(), 'bekliyor');
    END IF;
END$$

-- Temizlik tamamlaninca oda tekrar 'bos' olur
CREATE TRIGGER trg_temizlik_tamamlandi
AFTER UPDATE ON TemizlikKaydi
FOR EACH ROW
BEGIN
    IF NEW.durum = 'tamamlandi' AND OLD.durum <> 'tamamlandi' THEN
        UPDATE Oda SET durum = 'bos'
         WHERE oda_id = NEW.oda_id AND durum = 'temizlikte';
    END IF;
END$$

-- ---- TRIGGER 3: Rezervasyon ve Odeme degisikliklerini IslemLog'a yaz --
CREATE TRIGGER trg_rez_log_ins
AFTER INSERT ON Rezervasyon
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, yeni_deger)
    VALUES ('Rezervasyon', 'INSERT', NEW.rezervasyon_id,
            JSON_OBJECT('misafir_id', NEW.misafir_id, 'oda_id', NEW.oda_id,
                        'giris', NEW.giris_tarihi, 'cikis', NEW.cikis_tarihi,
                        'kisi', NEW.kisi_sayisi, 'durum', NEW.durum));
END$$

CREATE TRIGGER trg_rez_log_upd
AFTER UPDATE ON Rezervasyon
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, eski_deger, yeni_deger)
    VALUES ('Rezervasyon', 'UPDATE', NEW.rezervasyon_id,
            JSON_OBJECT('misafir_id', OLD.misafir_id, 'oda_id', OLD.oda_id,
                        'giris', OLD.giris_tarihi, 'cikis', OLD.cikis_tarihi,
                        'kisi', OLD.kisi_sayisi, 'durum', OLD.durum),
            JSON_OBJECT('misafir_id', NEW.misafir_id, 'oda_id', NEW.oda_id,
                        'giris', NEW.giris_tarihi, 'cikis', NEW.cikis_tarihi,
                        'kisi', NEW.kisi_sayisi, 'durum', NEW.durum));
END$$

CREATE TRIGGER trg_rez_log_del
AFTER DELETE ON Rezervasyon
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, eski_deger)
    VALUES ('Rezervasyon', 'DELETE', OLD.rezervasyon_id,
            JSON_OBJECT('misafir_id', OLD.misafir_id, 'oda_id', OLD.oda_id,
                        'giris', OLD.giris_tarihi, 'cikis', OLD.cikis_tarihi,
                        'kisi', OLD.kisi_sayisi, 'durum', OLD.durum));
END$$

CREATE TRIGGER trg_odeme_log_ins
AFTER INSERT ON Odeme
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, yeni_deger)
    VALUES ('Odeme', 'INSERT', NEW.odeme_id,
            JSON_OBJECT('konaklama_id', NEW.konaklama_id, 'tutar', NEW.tutar,
                        'odeme_turu', NEW.odeme_turu));
END$$

CREATE TRIGGER trg_odeme_log_upd
AFTER UPDATE ON Odeme
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, eski_deger, yeni_deger)
    VALUES ('Odeme', 'UPDATE', NEW.odeme_id,
            JSON_OBJECT('konaklama_id', OLD.konaklama_id, 'tutar', OLD.tutar,
                        'odeme_turu', OLD.odeme_turu),
            JSON_OBJECT('konaklama_id', NEW.konaklama_id, 'tutar', NEW.tutar,
                        'odeme_turu', NEW.odeme_turu));
END$$

CREATE TRIGGER trg_odeme_log_del
AFTER DELETE ON Odeme
FOR EACH ROW
BEGIN
    INSERT INTO IslemLog (tablo_adi, islem_turu, kayit_id, eski_deger)
    VALUES ('Odeme', 'DELETE', OLD.odeme_id,
            JSON_OBJECT('konaklama_id', OLD.konaklama_id, 'tutar', OLD.tutar,
                        'odeme_turu', OLD.odeme_turu));
END$$

DELIMITER ;

-- =====================================================================
-- 5) VIEW'LAR
-- =====================================================================

-- VIEW 1: Bugun giris ve cikis yapacak misafirler
CREATE VIEW vw_bugun_giris_cikis AS
SELECT 'GIRIS'                         AS islem_turu,
       r.rezervasyon_id,
       NULL                            AS konaklama_id,
       CONCAT(m.ad, ' ', m.soyad)      AS misafir,
       m.telefon,
       o.oda_no,
       r.giris_tarihi,
       r.cikis_tarihi
  FROM Rezervasyon r
  JOIN Misafir m ON m.misafir_id = r.misafir_id
  JOIN Oda o     ON o.oda_id     = r.oda_id
  LEFT JOIN Konaklama k ON k.rezervasyon_id = r.rezervasyon_id
 WHERE r.giris_tarihi = CURDATE()
   AND r.durum = 'onayli'
   AND k.konaklama_id IS NULL            -- henuz check-in yapilmamis
UNION ALL
SELECT 'CIKIS',
       r.rezervasyon_id,
       k.konaklama_id,
       CONCAT(m.ad, ' ', m.soyad),
       m.telefon,
       o.oda_no,
       r.giris_tarihi,
       r.cikis_tarihi
  FROM Konaklama k
  JOIN Rezervasyon r ON r.rezervasyon_id = k.rezervasyon_id
  JOIN Misafir m     ON m.misafir_id     = r.misafir_id
  JOIN Oda o         ON o.oda_id         = r.oda_id
 WHERE r.cikis_tarihi = CURDATE()
   AND k.gercek_cikis IS NULL;           -- henuz check-out yapilmamis

-- VIEW 2: Oda bazinda guncel durum ve son temizlik tarihi
CREATE VIEW vw_oda_durum AS
SELECT o.oda_id,
       o.oda_no,
       o.kat,
       ot.tip_adi,
       o.durum,
       (SELECT MAX(t.tarih)
          FROM TemizlikKaydi t
         WHERE t.oda_id = o.oda_id AND t.durum = 'tamamlandi') AS son_temizlik_tarihi
  FROM Oda o
  JOIN OdaTipi ot ON ot.tip_id = o.tip_id;
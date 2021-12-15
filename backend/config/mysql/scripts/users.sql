SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `users`
--

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `cc_number` varchar(255) NOT NULL,
  `given_name` varchar(255) NOT NULL,
  `surname` varchar(255) NOT NULL,
  `bio_data_location` varchar(255) NOT NULL,
  `has_facial` boolean NOT NULL,
  `has_fingerprint` boolean NOT NULL,
  PRIMARY KEY (`cc_number`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`cc_number`, `given_name`, `surname`, `bio_data_location`, `has_facial`, `has_fingerprint`) VALUES
('BI152665714', 'DUARTE', 'NEVES TAVARES MORTÁGUA', 'bio_data/BI152665714', 0, 0);

-- --------------------------------------------------------
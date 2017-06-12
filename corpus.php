<?php $argv;

if ( count( $argv ) < 1 ) {
	return false;
}

class Corpus {

	public $sounds = array(); # our sound files array
	private $db = null;

	function __construct() {
		self::config();
		self::db_connect();
		self::get_sounds();

		self::choose_adventure();
	}

	private function config() {
		require_once './config.php';
	}

	private function choose_adventure() {
		$options = array( 'Dictate', 'Update Corpus' );
		$chosen = $this->readline( $options );

		switch ( $chosen ) {
			case 'Update Corpus':
				self::verify_sounds();
				break;

			default:
				self::dictate();
				break;
		}
	}

	private function dictate() {
		$last_msg = '';

		$msg = $this->read_last_line( __DIR__ . '/words.log' );
		if( $msg !== $last_msg ) {
			$last_msg = $msg;
			echo $msg;
			echo PHP_EOL;
			$search = $this->full_text_search( $msg );

			if ( ! empty( $search ) && isset( $search['id'] ) ) {
				$meta = $this->get_dictionary_meta( $search['id'] );

				if ( ! empty( $meta ) && isset( $meta['sound_file'] ) ) {
					$this->play_sound( $meta['sound_file'] );
				}
			}
		}
		self::choose_adventure();
	}

	private function db_connect() {
		try {
			$args = array(
				'host' => DB_HOST,
				'dbname' => DB_NAME,
				'port' => DB_PORT,
			);

			$dsn_params = http_build_query( $args, null, ';' );
			$dsn = 'mysql:' . $dsn_params;

			$this->db = new PDO( $dsn, DB_USER, DB_PASSWORD );
			$this->db->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
		} catch( PDOException $e ) {
			echo "Connection failed: " . $e->getMessage();
		}
	}

	private function db_select( $query, $params = array() ) {
		try {
			$stmt = $this->db->prepare( $query );
			foreach ( $params as $key => &$value ) {
				$stmt->bindParam( $key+1, $value );
			}
			$stmt->execute();

			// set the resulting array to associative
			$stmt->setFetchMode( PDO::FETCH_ASSOC );
			return $stmt->fetch();

		} catch( PDOException $e ) {
			return false;
		}
	}

	private function db_insert( $query, $params = array() ) {
		try {
			$stmt = $this->db->prepare( $query );
			foreach ( $params as $key => &$value ) {
				$stmt->bindParam( $key+1, $value );
			}

			$stmt->execute();

			return $stmt->rowCount();
		} catch( PDOException $e ) {
			var_dump($e);
			return false;
		}
	}

	private function db_update( $query ) {
		try {
			$stmt = $this->db->prepare( $query );
			$stmt->execute();

			return $stmt->rowCount();

		} catch( PDOException $e ) {
			return false;
		}
	}

	private function full_text_search( $body ) {
		$query = 'SELECT * FROM dictionary WHERE MATCH (body) AGAINST (? IN NATURAL LANGUAGE MODE)';
		return $this->db_select( $query, array( $body ) );
	}

	private function get_dictionary_line( $text ) {
		$query = 'SELECT * FROM dictionary WHERE body = ? LIMIT 1';
		return $this->db_select( $query, array( $text ) );
	}

	private function get_dictionary_meta( $dict_id ) {
		$query = 'SELECT * FROM dictionary_meta WHERE dict_id = ? LIMIT 1';
		return $this->db_select( $query, array( $dict_id ) );
	}

	private function get_dictionary_from_sound( $sound ) {
		$query = 'SELECT dictionary.id, dictionary.body
  FROM dictionary INNER JOIN dictionary_meta ON (dictionary.id = dictionary_meta.dict_id)
  WHERE dictionary_meta.sound_file = ? LIMIT 1';
		return $this->db_select( $query, array( $sound ) );
	}

	private function update_dictionary_line( $body, $dict_id = null ) {

		#first check to see if this already exists.
		if ( empty( $dict_id ) ) {
			$results = $this->get_dictionary_line( $body );
			if ( empty( $results ) ) {
				$query = "INSERT INTO dictionary (id, body) VALUES (0, ?);";
				$result = $this->db_insert( $query, array( $body ) );
			}
		} else {
			$query = 'UPDATE dictionary SET body = ? WHERE id = ?;';
			$result = $this->db_insert( $query, array( $body, $dict_id ) );
		}

		if ( $result ) {
			$results = $this->get_dictionary_line( $body );
		}

		return $results;
	}

	private function update_dictionary_meta( $dict_id, $sound_file ) {

		#first check to see if this already exists.
		$results = $this->get_dictionary_meta( (int)$dict_id );

		if ( ! empty( $results ) && isset( $results['id'] ) ) {
			$query = 'UPDATE dictionary_meta SET dict_id = ?, sound_file = ? WHERE id = ?;';
			$result = $this->db_insert( $query, array( $dict_id, $sound_file, (int)$results['id'] ) );
		}else{
			$query = 'INSERT INTO dictionary_meta (id, dict_id, sound_file) VALUES (?, ?, ?);';
			$result = $this->db_insert( $query, array( 0, $dict_id, $sound_file ) );
		}

		if ( $result ) {
			$results = $this->get_dictionary_meta( $dict_id );
		}

		return $results;
	}

	private function get_sounds() {
		$this->sounds = glob( './sound/*.{wav}', GLOB_BRACE );
	}

	private function play_sound( $sound ) {
		exec( 'play ' . $sound );
	}

	public function verify_sound( $sound ) {
		$this->play_sound( $sound );
		$text = $this->sound_to_text( $sound );

		$options = array();

		$record_id = null;

		$record = $this->get_dictionary_from_sound( $sound );

		if ( ! empty( $record ) && isset( $record['body'] ) ) {
			$options[] = $record['body'];
			$record_id = $record['id'];
		}

		$options[] = $text;

		echo PHP_EOL . "Choose the following correct text or type in to fix: " . PHP_EOL;

		$correction = $this->readline( $options );

		echo PHP_EOL;

		$dict = $this->update_dictionary_line( $correction, $record_id );

		if ( ! empty( $dict ) && isset( $dict['id'] ) ) {
			$this->update_dictionary_meta( (int) $dict['id'], $sound );
		}
	}

	public function verify_sounds() {
		foreach ( $this->sounds as $sound ) {
			$this->verify_sound( $sound );
		}
	}

	private function sound_to_text( $sound ) {
		return exec( 'pocketsphinx_continuous -hmm /usr/local/share/pocketsphinx/model/en-us/en-us \
-lm ' . __DIR__ . '/corpus/' . CORPUS . '.lm \
-dict ' . __DIR__ . '/corpus/' . CORPUS . '.dic \
-samprate 16000/8000/48000 \
-infile ' . $sound . ' \
-logfn /dev/null');
	}

	private function dictate_to_text() {
		return exec( 'pocketsphinx_continuous -hmm /usr/local/share/pocketsphinx/model/en-us/en-us \
-lm ' . __DIR__ . '/corpus/' . CORPUS . '.lm \
-dict ' . __DIR__ . '/corpus/' . CORPUS . '.dic \
-samprate 16000/8000/48000 \
-inmic yes 2>' . __DIR__ . '/debug.log | tee ' . __DIR__ . '/words.log' );
	}

	private function readline( $options = array() ) {
		$readline = '';

		$options = array_filter( $options );
		$options = array_unique( $options );
		foreach ( $options as $key => $option ) {
			$readline .= "[$key] $option" . PHP_EOL;
		}

		$response = readline( $readline );

		$response_int = intval( $response );

		if ( 0 === strlen( $response )
			 || '0' === $response
			 || $response_int >= count( $options )
		) {
			return $options[0];
		} elseif ( 1 === strlen( $response ) # response length is exactly 1 character
			 && $response_int < count( $options ) # accepting integers within range of our options
			 && $response_int >= 0 # no negative numbers...
		) {
			return $options[ $response_int ];
		} elseif ( ! empty( $response ) && $response !== $transcription ) {
			return $response;
		} else {
			return $options[0];
		}
		return $options[0];
	}

	public function read_last_line( $file_path ) {

		$line = '';

		$f = fopen( $file_path, 'a+' );
		$cursor = -1;

		fseek( $f, $cursor, SEEK_END );
		$char = fgetc( $f );

		/**
		* Trim trailing newline chars of the file
		*/
		while ( "\n" === $char || "\r" === $char ) {
			fseek( $f, $cursor--, SEEK_END );
			$char = fgetc( $f );
		}

		/**
		* Read until the start of file or first newline char
		*/
		while ( false !== $char && "\n" !== $char && "\r" !== $char ) {
			/**
			* Prepend the new char
			*/
			$line = $char . $line;
			fseek( $f, $cursor--, SEEK_END );
			$char = fgetc( $f );
		}

		fclose( $f );

		return $line;
	}

}

$corpus = new Corpus();

<?php $argv;

if ( count( $argv ) < 1 ) {
	return false;
}

class Corpus {

	public $sounds = array(); # our sound files array
	private $db = null;
	private $path = '';

	function __construct() {
		self::config();
		self::db_connect();
		self::get_sounds();

		self::choose_adventure();
	}

	private function config() {
		$this->path = dirname( __FILE__ );
		require_once $this->path . '/config.php';
	}

	private function choose_adventure() {

		$options = array( 'Dictate', 'Verify New Sounds', 'Verify All Sounds' );
		$chosen = $this->readline( $options );

		switch ( $chosen ) {
			case 'Verify All Sounds':
				self::verify_sounds();
				break;
			case 'Verify New Sounds':
				self::asr_interpret_sounds();
				break;
			default:
				self::dictate();
				break;
		}
	}

	private function dictate() {
		$last_msg = '';

		$msg = $this->read_last_line( $this->path . '/words.log' );
		if ( $msg !== $last_msg ) {
			$last_msg = $msg;
			echo $msg;
			echo PHP_EOL;
			$search = $this->full_text_search( $msg );

			$id_values = $this->pluck( $search, 'id' );
			$body_values = $this->pluck( $search, 'body' );

			$option = $this->readline( $body_values );

			$id = array_search( $option, $body_values, true );

			if ( ! isset( $id_values[ $id ] ) ) {
				return false;
			}

			$meta_id = $id_values[ (int) $id ];

			$meta = $this->get_dictionary_meta( $meta_id );

			if ( ! empty( $meta ) && is_array( $meta ) ) {
				$sound_files = $this->pluck( $meta, 'sound_file' );

				$sound = $sound_files[ array_rand( $sound_files ) ];

				$this->play_sound( $sound );
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
		} catch ( PDOException $e ) {
			echo 'Connection failed: ' . $e->getMessage();
		}
	}

	private function db_select( $query, $params = array(), $fetch_mode = PDO::FETCH_ASSOC ) {
		try {
			$stmt = $this->db->prepare( $query );
			if ( ! empty( $params ) ) {
				foreach ( $params as $key => &$value ) {
					$stmt->bindParam( $key + 1, $value );
				}
			}
			$stmt->execute();

			// set the resulting array to associative
			$stmt->setFetchMode( $fetch_mode );
			return $stmt->fetchAll();

		} catch ( PDOException $e ) {
			return false;
		}
	}

	private function db_insert( $query, $params = array() ) {
		try {
			$stmt = $this->db->prepare( $query );
			foreach ( $params as $key => &$value ) {
				$stmt->bindParam( $key + 1, $value );
			}

			$stmt->execute();

			return $stmt->rowCount();
		} catch ( PDOException $e ) {
			var_dump( $e );
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
		$query = 'SELECT id, body, MATCH (body) AGAINST (? IN NATURAL LANGUAGE MODE) AS score FROM dictionary WHERE MATCH (body) AGAINST (? IN NATURAL LANGUAGE MODE) ORDER BY score DESC';
		//$query = 'SELECT * FROM dictionary WHERE MATCH (body) AGAINST (? IN NATURAL LANGUAGE MODE)';
		$result = $this->db_select( $query, array( $body, $body ) );

		if( ! empty( $result ) && is_array( $result ) ) {
			return $result;
		}
		return false;
	}

	private function get_dictionary_line( $text ) {
		$query = 'SELECT * FROM dictionary WHERE body = ? LIMIT 1';
		$result = $this->db_select( $query, array( $text ) );

		if( ! empty( $result ) && is_array( $result ) ) {
			return $result[0];
		}

		return false;
	}

	private function get_dictionary_meta( $dict_id ) {
		$query = 'SELECT * FROM dictionary_meta WHERE dict_id = ? LIMIT 1';
		return $this->db_select( $query, array( (int) $dict_id ) );
	}

	private function get_dictionary_sounds() {
		$output = array();
		$query = 'SELECT dictionary_meta.sound_file
  FROM dictionary INNER JOIN dictionary_meta ON (dictionary.id = dictionary_meta.dict_id)';
		$result = $this->db_select( $query, array(), PDO::FETCH_NAMED );

		foreach ( $result as $key => $value ) {
			$output[] = $value[ 'sound_file' ];
		}

		return $output;
	}

	private function get_dictionary_from_sound( $sound ) {
		$sound = $this->get_relative_sound_path( $sound );
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
				$query = 'INSERT INTO dictionary (id, body) VALUES (0, ?);';
				$result = $this->db_insert( $query, array( $body ) );
			}
		} else {
			$query = 'UPDATE dictionary SET body = ? WHERE id = ?;';
			$result = $this->db_insert( $query, array( $body, (int) $dict_id ) );
		}

		if ( $result ) {
			$results = $this->get_dictionary_line( $body );
		}

		return $results;
	}

	private function update_dictionary_meta( $dict_id, $sound_file ) {
		#first check to see if this already exists.
		$results = $this->get_dictionary_meta( (int) $dict_id );

		$relative_path = str_replace( $this->path, '', $sound_file );

		if ( ! empty( $results ) && isset( $results['id'] ) ) {
			$query = 'UPDATE dictionary_meta SET dict_id = ?, sound_file = ? WHERE id = ?;';
			$result = $this->db_insert( $query, array( $dict_id, $relative_path, (int) $results['id'] ) );
		} else {
			$query = 'INSERT INTO dictionary_meta (id, dict_id, sound_file) VALUES (?, ?, ?);';
			$result = $this->db_insert( $query, array( 0, $dict_id, $relative_path ) );
		}

		if ( $result ) {
			$results = $this->get_dictionary_meta( $dict_id );
		}

		return $results;
	}

	private function get_sounds() {
		if ( empty( $this->sounds ) ) {
			$this->sounds = glob( $this->path . '/sound/*.{wav}', GLOB_BRACE );
		}

		return $this->sounds;
	}

	private function get_full_sound_path( $sound ) {
		if ( false === strpos( $sound, $this->path ) ) {
			$sound = $this->path . $sound;
		}

		if ( ! file_exists( $sound ) ) {
			return false;
		}

		return $sound;
	}

	private function get_relative_sound_path( $sound ) {
		return str_replace( $this->path, '', $sound);
	}

	private function play_sound( $sound ) {
		$sound = $this->get_full_sound_path( $sound );

		if ( ! $sound ) {
			return false;
		}

		exec( 'play ' . $sound );
	}

	public function verify_sound( $sound ) {

		$sound = $this->get_full_sound_path( $sound );

		if ( ! file_exists( $sound ) ) {
			return false;
		}

		$this->play_sound( $sound );
		$text = $this->sound_to_text( $sound );

		$options = array();

		$record_id = null;

		$record = $this->get_dictionary_from_sound( $sound );

		if ( ! empty( $record ) && is_array( $record ) ) {
			foreach ( $record as $r ) {
				$options[] = $r['body'];
				$record_id = $r['id'];
			}
		}

		$options[] = $text;

		echo PHP_EOL . 'Choose the following correct text or type in to fix: ' . PHP_EOL;

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

	public function asr_interpret_sounds() {
		$all_sounds = str_replace( $this->path, '', $this->sounds );
		$dictionary_sounds = $this->get_dictionary_sounds();

		$sounds = array_values( array_diff( $all_sounds, $dictionary_sounds ) );

		foreach ( $sounds as $sound ) {
			$this->verify_sound( $sound );
		}
	}

	private function sound_to_text( $sound ) {
		return exec( 'pocketsphinx_continuous -hmm /usr/local/share/pocketsphinx/model/en-us/en-us \
-lm ' . $this->path . '/corpus/' . CORPUS . '.lm \
-dict ' . $this->path . '/corpus/' . CORPUS . '.dic \
-samprate 16000/8000/48000 \
-infile ' . $sound . ' \
-logfn /dev/null');
	}

	private function dictate_to_text() {
		return exec( 'pocketsphinx_continuous -hmm /usr/local/share/pocketsphinx/model/en-us/en-us \
-lm ' . $this->path . '/corpus/' . CORPUS . '.lm \
-dict ' . $this->path . '/corpus/' . CORPUS . '.dic \
-samprate 16000/8000/48000 \
-inmic yes 2>' . $this->path . '/debug.log | tee ' . $this->path . '/words.log' );
	}

	private function readline( $options = array() ) {
		$readline = '';

		$options = array_filter( $options );
		$options = array_unique( $options );
		foreach ( $options as $key => $option ) {
			# $option = filter_var ( $option, FILTER_SANITIZE_STRING );
			if ( 120 < strlen( $option ) ) {
				$option = substr( $option, 0, 120 );
				$option .= '...';
			}
			$readline .= "[$key] $option" . PHP_EOL;
		}

		$response = readline( $readline );

		if ( empty( $options ) ) {
			return $response;
		}

		if ( empty( $response ) ) {
			$response = 0;
		}

		if ( is_numeric( $response ) ) {
			$response = intval( $response );
		}

		if ( is_int( $response ) && isset( $options[ $response ] ) ) {
			return $options[ $response ];
		}elseif ( ! empty( $response ) && $response !== $transcription ) {
			return $response;
		}

		return $options[0];
	}

	public function read_last_line( $file_path ) {

		$line = '';

		$f = fopen( $file_path, 'r' );
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

	public function pluck( $list, $field, $index_key = null ) {
		if ( ! $index_key ) {
			/*
			 * This is simple. Could at some point wrap array_column()
			 * if we knew we had an array of arrays.
			 */
			foreach ( $list as $key => $value ) {
				if ( is_object( $value ) ) {
					$list[ $key ] = $value->$field;
				} else {
					$list[ $key ] = $value[ $field ];
				}
			}
			return $list;
		}

		/*
		 * When index_key is not set for a particular item, push the value
		 * to the end of the stack. This is how array_column() behaves.
		 */
		$newlist = array();

		$this->output = $newlist;

		return $this->output;
	}

}

$corpus = new Corpus();

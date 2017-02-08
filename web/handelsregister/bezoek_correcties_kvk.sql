SELECT
        l.correctie_level,
	v.naam,
	m.kvk_nummer,
	v.vestigingsnummer,
	v.hoofdvestiging,
	l.bag_vbid,
	l.bag_numid,
	l.volledig_adres, 
	l.query_string from hr_locatie l 
	JOIN hr_vestiging v ON v.bezoekadres_id = l.id
	JOIN hr_maatschappelijkeactiviteit m ON m.id = v.maatschappelijke_activiteit_id
	WHERE 
	l.correctie = true ORDER BY l.correctie_level;
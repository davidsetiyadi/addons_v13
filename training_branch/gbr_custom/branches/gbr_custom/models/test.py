a = """SELECT move.id as move_id , line.id as move_line_id,rec_line.id as rec_id, payment.id as payment_id 
	FROM account_move move
	JOIN account_move_line line ON line.move_id = move.id
	JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
	JOIN account_move_line rec_line ON
		(rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
		OR
		(rec_line.id = part.debit_move_id AND line.id = part.credit_move_id) 
	JOIN account_payment payment ON payment.id = rec_line.payment_id
	JOIN account_journal journal ON journal.id = rec_line.journal_id
	WHERE payment.state IN ('posted', 'sent')
	AND journal.post_at = 'pay_val' 	
	AND move.id = 39 ;
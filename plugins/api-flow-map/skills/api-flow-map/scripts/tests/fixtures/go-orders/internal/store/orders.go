package store

import (
	"context"
	"database/sql"
)

type Item struct{ SKU string; Qty int }
type Order struct{ ID, Status, PaymentID string; Total int; Items []Item }

func NewOrder(items []Item) *Order { return &Order{Items: items} }

type OrderStore struct{ db *sql.DB }

func (st *OrderStore) FindByID(ctx context.Context, id string) (*Order, error) {
	row := st.db.QueryRowContext(ctx, "SELECT id, status, total FROM orders WHERE id = $1", id)
	var o Order
	if err := row.Scan(&o.ID, &o.Status, &o.Total); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	return &o, nil
}

func (st *OrderStore) Save(ctx context.Context, o *Order) error {
	_, err := st.db.ExecContext(ctx, "INSERT INTO orders (id, status, total) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET status = $2", o.ID, o.Status, o.Total)
	return err
}

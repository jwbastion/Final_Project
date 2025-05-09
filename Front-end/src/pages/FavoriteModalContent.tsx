import React from 'react';

type Props = {
  listingId: number;
};

export default function FavoriteModalContent({ listingId }: Props) {
  // listingId로 DB에서 상세정보를 fetch하거나, props로 데이터 전달받아 렌더링
  // 예시: const { data, isLoading } = useQuery(['listingDetail', listingId], fetchListingDetail);

  // 임시: 준비중입니다
  return (
    <div style={{ fontSize: '1.1rem', fontWeight: 500 }}>
      준비중입니다
    </div>
  );
}
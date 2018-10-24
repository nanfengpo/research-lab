package how.monero.hodl.crypto;

import org.bouncycastle.jce.ECNamedCurveTable;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.jce.spec.ECParameterSpec;
import org.bouncycastle.math.ec.ECPoint;

import java.security.Security;

import java.util.Arrays;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;

import static how.monero.hodl.crypto.CryptoUtil.hashToScalar;
import static how.monero.hodl.util.ByteUtil.bytesToHex;

public class Curve25519Point {

  public static ECParameterSpec ecsp;

  static {
    try {
      Security.addProvider(new BouncyCastleProvider());
      ecsp = ECNamedCurveTable.getParameterSpec("curve25519");
    }
    catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  public ECPoint point; // 这个是主要的数据成员，表示椭圆曲线上的一个点
  public Curve25519Point(ECPoint point) {
    this.point = point;
  }
  public Curve25519Point(byte[] a) {
    this.point = ecsp.getCurve().decodePoint(a);
  }

  // 生成随机点。使用生成点BASE_POINT乘以一个随机标量Scalar.randomScalar()
  public static Curve25519Point randomPoint() {
    return BASE_POINT.scalarMultiply(Scalar.randomScalar());
  }
  
  // 点point乘以一个标量，即point*a。这个a往往是私密的
  public Curve25519Point scalarMultiply(Scalar a) {
    scalarMults++;
    if(this==BASE_POINT) scalarBaseMults++;

    if(enableLineRecording) {
       Optional<StackTraceElement> optionalCaller = Arrays.stream(new Exception().getStackTrace()).filter(e -> e.getFileName().equals(lineRecordingSourceFile)).findFirst();
       if (optionalCaller.isPresent()) {
         StackTraceElement caller = optionalCaller.get();
         lineNumberCallFrequencyMap.putIfAbsent(caller.getLineNumber(), 0);
         lineNumberCallFrequencyMap.computeIfPresent(caller.getLineNumber(), (key, oldValue) -> oldValue + 1);
       }
     }

    return new Curve25519Point(point.multiply(a.toBigInteger()));
  }
  
  // 点point加另一个点a
  public Curve25519Point add(Curve25519Point a) {
    return new Curve25519Point(point.add(a.point));
  }
  
  // 点point减另一个点a
  public Curve25519Point subtract(Curve25519Point a) {
    return new Curve25519Point(point.subtract(a.point));
  }
  
  public byte[] toBytes() {
    return point.getEncoded(true);
  }
  
  public boolean satisfiesCurveEquation() {
    return true;
  }
  
  public static Curve25519Point hashToPoint(byte[] a) {
    return BASE_POINT.scalarMultiply(hashToScalar(a));
  }
  
  public static Curve25519Point hashToPoint(Curve25519Point a) {
    return hashToPoint(a.toBytes());
  }

  @Override
  public String toString() {
    return bytesToHex(toBytes());
  }

  // 获得椭圆曲线的零点，也就是无限的那个点。
  public static Curve25519Point ZERO = new Curve25519Point(ecsp.getCurve().getInfinity());
  // 获得椭圆曲线的生成点BASE_POINT
  public static Curve25519Point BASE_POINT = new Curve25519Point(ecsp.getG());
  public static Curve25519Point G = BASE_POINT;

  public static int scalarMults = 0;
 	public static int scalarBaseMults = 0;

  public static String lineRecordingSourceFile = null;
  public static boolean enableLineRecording = false;
 	public static Map<Integer, Integer> lineNumberCallFrequencyMap = new TreeMap<>((a, b)->a.compareTo(b));


  @Override
  public boolean equals(Object obj) {
    return point.equals(((Curve25519Point) obj).point);
  }
}

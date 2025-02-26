import Matter from 'matter-js';

window.Matter = Matter;

function initSlingshot() {
    var Example = window.Example || {};

    Example.slingshot = function () {
        var Engine = Matter.Engine,
            Render = Matter.Render,
            Runner = Matter.Runner,
            Composites = Matter.Composites,
            Events = Matter.Events,
            Constraint = Matter.Constraint,
            MouseConstraint = Matter.MouseConstraint,
            Mouse = Matter.Mouse,
            Body = Matter.Body,
            Composite = Matter.Composite,
            Bodies = Matter.Bodies;

        // create engine
        var engine = Engine.create(),
            world = engine.world;

        // create renderer
        var render = Render.create({
            element: document.body,
            engine: engine,
            options: {
                width: 1000,
                height: 800,
                showAngleIndicator: true
            }
        });

        Render.run(render);

        // create runner
        var runner = Runner.create();
        Runner.run(runner, engine);

        // エンジン設定を調整して衝突検出精度を向上
        engine.positionIterations = 10;  // デフォルトより高い値（デフォルト: 6）
        engine.velocityIterations = 10;  // デフォルトより高い値（デフォルト: 4）

        // 画面の端に壁を追加
        var wallOptions = {
            isStatic: true,
            render: { fillStyle: '#060a19' },
            restitution: 0.6,  // 跳ね返り係数を設定
            chamfer: { radius: 0 },  // 角を鋭角に
            slop: 0  // 衝突時の許容誤差を小さく
        };

        // 壁を少し厚くして貫通しにくくする
        var ground = Bodies.rectangle(500, 800, 1010, 50, wallOptions);
        var leftWall = Bodies.rectangle(-25, 400, 50, 800, wallOptions);
        var rightWall = Bodies.rectangle(1025, 400, 50, 800, wallOptions);
        var topWall = Bodies.rectangle(500, -25, 1010, 50, wallOptions);

        // ボールの初期位置を中央寄りに
        var rock = Bodies.polygon(250, 600, 8, 20, rockOptions);
        var anchor = { x: 250, y: 600 };

        // ボールの初期位置を中央寄りに
        var rockOptions = {
            density: 0.004,
            frictionAir: 0.005,
            restitution: 0.6,  // 跳ね返り係数を上げる
            render: {
                fillStyle: '#F35e66',  // 赤みがかったピンク色
                strokeStyle: 'black',
                lineWidth: 1
            }
        };

        // 多角形から円に変更
        var rock = Bodies.circle(170, 450, 20, rockOptions);

        var anchor = { x: 170, y: 450 };
        var elastic = Constraint.create({
            pointA: anchor,
            bodyB: rock,
            length: 0.01,
            damping: 0.01,
            stiffness: 0.05
        });

        var pyramid = Composites.pyramid(500, 300, 9, 10, 0, 0, function (x, y) {
            return Bodies.rectangle(x, y, 25, 40);
        });

        var ground2 = Bodies.rectangle(610, 250, 200, 20, { isStatic: true, render: { fillStyle: '#060a19' } });

        var pyramid2 = Composites.pyramid(550, 0, 5, 10, 0, 0, function (x, y) {
            return Bodies.rectangle(x, y, 25, 40);
        });

        // 全ての物体をワールドに追加
        Composite.add(engine.world, [
            ground, leftWall, rightWall, topWall,
            pyramid, ground2, pyramid2, rock, elastic
        ]);

        // ボールの状態を管理するフラグ
        var rockLaunched = false;
        var waitForRockToStop = false;

        Events.on(engine, 'afterUpdate', function () {
            // ボールが発射されたかチェック
            if (mouseConstraint.mouse.button === -1 && !rockLaunched && !waitForRockToStop &&
                elastic.bodyB === rock &&
                Body.getSpeed(rock) > 2) {
                rockLaunched = true;
                elastic.bodyB = null;
                elastic.render.visible = false;
            }

            // ボールが発射され、速度が十分低くなり、地面に近い場合のみ停止処理を行う
            if (rockLaunched && Body.getSpeed(rock) < 0.2) {
                waitForRockToStop = true;

                // すべての動いているオブジェクトを停止させる
                setTimeout(function () {
                    // ボールを完全に停止させる
                    Body.setVelocity(rock, { x: 0, y: 0 });
                    Body.setAngularVelocity(rock, 0);

                    // すべてのrectangleブロックも停止させる
                    var bodies = Composite.allBodies(world);
                    for (var i = 0; i < bodies.length; i++) {
                        var body = bodies[i];
                        if (!body.isStatic) {
                            Body.setVelocity(body, { x: 0, y: 0 });
                            Body.setAngularVelocity(body, 0);
                        }
                    }

                    // アンカーポイントを更新
                    anchor.x = rock.position.x;
                    anchor.y = rock.position.y;

                    // エラスティックのアンカーポイントも更新して再接続
                    elastic.pointA = anchor;
                    elastic.bodyB = rock;
                    elastic.render.visible = true;

                    // 発射フラグをリセット
                    rockLaunched = false;
                    waitForRockToStop = false;
                }, 300);  // 少し待ってから停止処理
            }
        });

        // add mouse control
        var mouse = Mouse.create(render.canvas),
            mouseConstraint = MouseConstraint.create(engine, {
                mouse: mouse,
                constraint: {
                    stiffness: 0.2,
                    render: {
                        visible: false
                    }
                }
            });

        Composite.add(world, mouseConstraint);

        // keep the mouse in sync with rendering
        render.mouse = mouse;

        // fit the render viewport to the scene
        Render.lookAt(render, {
            min: { x: 0, y: 0 },
            max: { x: 1000, y: 800 }
        });

        return {
            engine: engine,
            runner: runner,
            render: render,
            canvas: render.canvas,
            stop: function () {
                Matter.Render.stop(render);
                Matter.Runner.stop(runner);
            }
        };
    };

    window.Example = Example;
    Example.slingshot();
}

// DOMが読み込まれた後に実行
document.addEventListener('DOMContentLoaded', initSlingshot);